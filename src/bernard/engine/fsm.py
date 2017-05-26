# coding: utf-8
import asyncio
import importlib
from typing import List, Tuple, Type, Optional, Text, Iterator, Dict
from bernard.conf import settings
from bernard.utils import import_class
from bernard.storage.register import BaseRegisterStore, Register
from .transition import Transition
from .triggers import BaseTrigger
from .state import BaseState
from .request import Request, BaseMessage
from .responder import Responder


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

    async def _find_trigger(self, request: Request) \
            -> Optional[Tuple[
                Optional[BaseTrigger],
                Optional[Type[BaseState]],
            ]]:
        """
        Find the best trigger for this request, or go away.
        """

        reg = request.register
        origin = reg.get(Register.STATE)
        results = await asyncio.gather(*(
            x.rank(request, origin)
            for x
            in self.transitions
        ))
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
                           message: BaseMessage,
                           responder: Responder,
                           reg: Register) \
            -> Tuple[BaseState, BaseTrigger, Request]:
        """
        Build the state for this request.
        """

        request = Request(message, reg)
        trigger, state_class = await self._find_trigger(request)

        if trigger is None:
            state_class = self._confused_state(request)

        state = state_class(request, responder)
        return state, trigger, request

    async def _run_state(self, responder, state, trigger):
        """
        Execute the state, or if execution fails handle it.
        """

        # noinspection PyBroadException
        try:
            if trigger:
                await state.handle()
            else:
                await state.confused()
        except Exception:
            # todo handle exception
            responder.clear()
            await state.error()

    def _build_state_register(self,
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
            Register.TRANSITION: responder.make_transition_register(request),
        }

    async def _handle_message(self,
                              message: BaseMessage,
                              responder: Responder) -> Dict:
        """
        Handles a message: find a state and run it.

        :return: The register that was saved
        """

        reg_manager = self.register\
            .work_on_register(message.get_conversation().id)

        async with reg_manager as reg:
            state, trigger, request = \
                await self._build_state(message, responder, reg)
            await self._run_state(responder, state, trigger)
            await responder.flush(request)

            reg.replacement = \
                self._build_state_register(state, request, responder)
            return reg.replacement

    def handle_message(self,
                       message: BaseMessage,
                       responder: Responder,
                       create_task: True):
        """
        Public method to handle a message. It requires:

            - A message from the platform
            - A responder from the platfrom

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
