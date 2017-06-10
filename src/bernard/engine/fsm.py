# coding: utf-8
import asyncio
import importlib
import logging
from typing import List, Tuple, Type, Optional, Text, Iterator, Dict
from bernard.conf import settings
from bernard.i18n.translator import MissingTranslationError
from bernard.utils import import_class
from bernard.storage.register import BaseRegisterStore, Register
from bernard.reporter import reporter
from bernard.layers import RawText
from .transition import Transition
from .triggers import BaseTrigger
from .state import BaseState
from .request import Request, BaseMessage
from .responder import Responder


logger = logging.getLogger('bernard.fsm')


class FsmError(Exception):
    """
    Base FSM exception
    """


class MaxInternalJump(FsmError):
    """
    That's when the max number of internal jumps is reached
    """


class FSM(object):
    """
    The FSM is the core of the engine. FSM as in "Finite-State Machine".

    Bots are represented as a FSM: states are the various states of the but,
    and each state handler sends messages to the user. Transitions are
    triggered by events from the user (or crons, or whatever).

    There is a transitions file that describes all possible transitions. When
    an event occurs, all transitions are polled to see if a trigger emerges.

    For each conversation, there is a register of the current state.
    """

    def __init__(self):
        self.register = self._make_register()
        self.transitions = self._make_transitions()
        self._allowed_states = set(self._make_allowed_states())

    async def async_init(self):
        """
        THe register might need to be initialized in a loop
        """

        await self.register.async_init()

    def _make_register(self) -> BaseRegisterStore:
        """
        Make the register storage.
        """

        s = settings.REGISTER_STORE
        store_class = import_class(s['class'])
        return store_class(**s['params'])

    def _make_transitions(self) -> List[Transition]:
        """
        Load the transitions file.
        """

        module_name = settings.TRANSITIONS_MODULE
        module_ = importlib.import_module(module_name)
        return module_.transitions

    def _make_allowed_states(self) -> Iterator[Text]:
        """
        Sometimes we load states from the database. In order to avoid loading
        an arbitrary class, we list here the state classes that are allowed.
        """

        for trans in self.transitions:
            yield trans.dest.name()

            if trans.origin:
                yield trans.origin.name()

    async def _find_trigger(self,
                            request: Request,
                            origin: Optional[Text]=None,
                            internal: bool=False) \
            -> Tuple[
                Optional[BaseTrigger],
                Optional[Type[BaseState]],
            ]:
        """
        Find the best trigger for this request, or go away.
        """

        reg = request.register

        if not origin:
            origin = reg.get(Register.STATE)
            logger.debug('From state: %s', origin)

        results = await asyncio.gather(*(
            x.rank(request, origin)
            for x
            in self.transitions
            if x.internal == internal
        ))

        if len(results):
            score, trigger, state = max(results, key=lambda x: x[0])

            if score >= settings.MINIMAL_TRIGGER_SCORE:
                return trigger, state

        return None, None

    # noinspection PyTypeChecker
    def _confused_state(self, request: Request) -> Type[BaseState]:
        """
        If we're confused, find which state to call.
        """

        origin = request.register.get(Register.STATE)

        if origin in self._allowed_states:
            try:
                return import_class(origin)
            except (AttributeError, ImportError):
                pass

        return import_class(settings.DEFAULT_STATE)

    async def _build_state(self,
                           request: Request,
                           message: BaseMessage,
                           responder: Responder) \
            -> Tuple[
                Optional[BaseState],
                Optional[BaseTrigger],
            ]:
        """
        Build the state for this request.
        """

        logger.debug('Incoming message: %s', request.stack)
        trigger, state_class = await self._find_trigger(request)

        if trigger is None:
            if not message.should_confuse():
                return None, None
            state_class = self._confused_state(request)
            logger.debug('Next state: %s (confused)', state_class.name())
        else:
            logger.debug('Next state: %s', state_class.name())

        state = state_class(request, responder, trigger)
        return state, trigger

    async def _run_state(self, responder, state, trigger, request) \
            -> BaseState:
        """
        Execute the state, or if execution fails handle it.
        """

        # noinspection PyBroadException
        try:
            if trigger:
                await state.handle()
            else:
                await state.confused()

            for i in range(0, settings.MAX_INTERNAL_JUMPS + 1):
                if i == settings.MAX_INTERNAL_JUMPS:
                    raise MaxInternalJump()

                trigger, state_class = \
                    await self._find_trigger(request, state.name(), True)

                if not trigger:
                    break

                logger.debug('Jumping to state: %s', state_class.name())
                state = state_class(request, responder)
                await state.handle()
        except Exception:
            logger.exception('Error while handling state "%s"', state.name())
            responder.clear()
            reporter.report(request, state.name())
            await state.error()

        return state

    async def _build_state_register(self,
                              state: BaseState,
                              request: Request,
                              responder: Responder) -> Dict:
        """
        Build the next register to store.

            - The state is the name of the current state
            - The transition is made by all successive layers present in the
              response.
        """

        return {
            Register.STATE: state.name(),
            Register.TRANSITION:
                await responder.make_transition_register(request),
        }

    async def _handle_message(self,
                              message: BaseMessage,
                              responder: Responder) -> Optional[Dict]:
        """
        Handles a message: find a state and run it.

        :return: The register that was saved
        """

        reg_manager = self.register\
            .work_on_register(message.get_conversation().id)

        async with reg_manager as reg:
            request = Request(message, reg)
            await request.transform()

            try:
                state, trigger = \
                    await self._build_state(request, message, responder)
            except Exception:
                reporter.report(request, None)
                logger.exception('Error while finding a transition from %s',
                                 reg.get(Register.STATE))
                return

            if state is None:
                return

            state = await self._run_state(responder, state, trigger, request)

            # noinspection PyBroadException
            try:
                await responder.flush(request)
            except MissingTranslationError as e:
                responder.clear()
                responder.send([RawText(str(e))])
                await responder.flush(request)

                reporter.report(request, state.name())
                logger.exception('Missing translation in state %s',
                                 state.name())
            except Exception:
                reporter.report(request, state.name())
                logger.exception('Could not flush content after %s',
                                 state.name())
            else:
                reg.replacement = \
                    await self._build_state_register(state, request, responder)
                return reg.replacement

    def handle_message(self,
                       message: BaseMessage,
                       responder: Responder,
                       create_task: True):
        """
        Public method to handle a message. It requires:

            - A message from the platform
            - A responder from the platform

        If `create_task` is true, them the task will automatically be added to
        the loop. However, if it is not, the coroutine will be returned and it
        will be the responsibility of the caller to run/start the task.
        """

        coro = self._handle_message(message, responder)

        if create_task:
            loop = asyncio.get_event_loop()
            loop.create_task(coro)
        else:
            return coro
