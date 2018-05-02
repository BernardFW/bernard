# coding: utf-8
import importlib
import logging
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Type,
)

from bernard.conf import (
    settings,
)
from bernard.core.health_check import (
    HealthCheckFail,
)
from bernard.i18n.translator import (
    MissingTranslationError,
)
from bernard.layers import (
    RawText,
)
from bernard.reporter import (
    reporter,
)
from bernard.storage.register import (
    Register,
)
from bernard.utils import (
    import_class,
)

from ._base import (
    TransitionManager,
    UpcomingState,
)
from .request import (
    Request,
)
from .responder import (
    Responder,
)
from .state import (
    BaseState,
    DefaultState,
)
from .transition import (
    Target,
    Transition,
)

logger = logging.getLogger('bernard.engine.app')


def _make_target_name(target: Target):
    """
    For a given target, generate a printable name for the logs
    """

    if target:
        return target.name()
    else:
        return '(init)'


class CallStack(object):
    """
    Prototype API for the call stack, not in use yet.
    """

    async def push(self, app: 'BaseApp', args):
        pass  # TODO

    async def pop(self, return_value: Any):
        pass  # TODO

    async def run(self):
        pass  # TODO


class BaseApp(object):
    """
    This is the base app class that you should implement when creating your
    own app. You could by example delegate the handing of messages to an
    external service, like a chat with an actual human.
    """

    def __init__(self):
        """
        Yes, you should call super() even if this init does nothing. Who knows
        what will happen in the future!
        """

    async def handle_message(self,
                             call_stack: CallStack,
                             request: Request,
                             responder: Responder,
                             args: Any) -> Optional[Dict]:
        """
        Implement this method to handle incoming messages. From there you can
        do whatever you want to handle the message, using the provided tools.

        :param call_stack: Current call stack. You can push or pop things from
                           it if it makes sense in your app (like sub-FSMs).
        :param request: Completely built request that you can use, including
                        the register.
        :param responder: Responder to call for message sending.
        :param args: Args you were called with
        :return: TODO why the fuck is there a return value?
        """

        raise NotImplementedError


class FsmApp(BaseApp):
    """
    An app class to implement an FSM. This is the main idea onto which
    BERNARD was built. If you want to use it, you need to inherit from it and
    set your own values to `transitions` and `default_state`.
    """

    transitions: List[Transition] = None
    default_state: Type[BaseState] = None

    def __init__(self):
        """
        Creates the transitions manager.
        """

        super().__init__()
        self.tm = TransitionManager(self.transitions, self.default_state)

    async def health_check(self) -> AsyncIterator[HealthCheckFail]:
        """
        Checks that this instance makes sense:

        - The default state should be defined and valid
        - Transitions should have been defined
        - Also run health check in all states
        """

        ds_is_forbidden = not self.default_state \
            or self.default_state == DefaultState \
            or not issubclass(self.default_state, BaseState)

        app_name = self.__class__.__name__

        if ds_is_forbidden:
            yield HealthCheckFail(
                '00006',
                f'In your app {app_name}, the default state is '
                f'{_make_target_name(self.default_state)}, which is forbidden.'
                f' You need to create your own default state and set it '
                f'`{app_name}.default_state`.'
            )

        if self.transitions is None:
            yield HealthCheckFail(
                '00006',
                f'It looks like {app_name}.transitions is not set. Please put '
                f'the transitions for your app in there!',
            )

        states = set(t.dest for t in self.transitions)

        for state in states:
            async for check in state.health_check():
                yield check

    async def run_state(self,
                        state: BaseState,
                        request: Request,
                        responder: Responder,
                        upcoming: UpcomingState) -> BaseState:
        """
        Runs a state. If internal transitions are triggered, also run the
        following states until there is no more internal transitions or the
        jump limit is exceeded (we wouldn't want an infinite loop, right?).

        :param state: State to run (not necessarily the one from upcoming!)
        :param request: Request
        :param responder: Responder
        :param upcoming: Upcoming meta-data
        :return: Last-ran state, to get information for the register
        """

        user_trigger = upcoming.trigger

        if upcoming.trigger:
            await state.handle()
        else:
            await state.confused()

        for i in range(0, settings.MAX_INTERNAL_JUMPS + 1):
            if i == settings.MAX_INTERNAL_JUMPS:
                raise RecursionError('Too many internal state jumps')

            rank = await self.tm.find_trigger(
                request,
                upcoming.state.name(),
                True,
            )

            if not rank.trigger:
                break

            logger.debug('Jumping to state "%s"', rank.dest.name())
            state = rank.dest(request, responder, rank.trigger, user_trigger)
            await state.handle()

        return state

    async def build_register(self,
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

    # noinspection PyBroadException
    async def handle_message(self,
                             call_stack: CallStack,
                             request: Request,
                             responder: Responder,
                             args: Any) -> Optional[Dict]:
        """
        Handles an incoming message. Cf parent's doc for arguments.

        The message will get analyzed, located in the FSM and transitioned to
        the next most probable state. All potential errors should be caught,
        logged and sent to the error reporting system.

        The code looks long but actually most of the code is just error
        handling.
        """

        try:
            upcoming = await self.tm.build_upcoming(request)
        except Exception:
            logger.exception(
                'Error while finding a transition for %s',
                request.register.get(Register.STATE)
            )
            reporter.report(request, None)
            return

        if upcoming.state is None:
            logger.debug(
                'No next step found, but "%s" is not confusing',
                request.message,
            )
            return

        if upcoming.trigger:
            origin = _make_target_name(upcoming.transition_origin)

            if upcoming.transition_origin != upcoming.actual_origin:
                origin += f' (as {_make_target_name(upcoming.actual_origin)})'

            logger.debug(
                'Triggering %s -> %s (%s %s%%)',
                origin,
                _make_target_name(upcoming.state),
                upcoming.trigger.__class__.__name__,
                (upcoming.score * 1000.0) / 10.0,
            )
        else:
            logger.debug('Confused at %s', _make_target_name(upcoming.state))

        state = upcoming.state(
            request,
            responder,
            upcoming.trigger,
            upcoming.trigger,
        )

        try:
            state = await self.run_state(state, request, responder, upcoming)
        except Exception:
            logger.exception(
                'Something bad happened when handling "%s"',
                upcoming.state.name(),
            )
            reporter.report(request, state.name())

            try:
                responder.clear()
                await state.error()
                return
            except Exception:
                reporter.report(request, upcoming)
                logger.exception(
                    'Error while handling the error with "%s"',
                    upcoming.state.name(),
                )
                responder.clear()
                responder.send([RawText(str('⚠️ Internal Error'))])
                await responder.flush(request)
                return

        try:
            await responder.flush(request)
        except MissingTranslationError as e:
            responder.clear()
            responder.send([RawText(str(e))])
            await responder.flush(request)

            reporter.report(request, state.name())
            logger.exception(
                f'{e} in state %s',
                state.name(),
            )
            return
        except Exception:
            reporter.report(request, state.name())
            logger.exception('Could not flush content of "%s"', state.name())
            return
        else:
            if not upcoming.dnr:
                request.register.replacement = await self.build_register(
                    state,
                    request,
                    responder,
                )
            return request.register.replacement


class RootApp(FsmApp):
    """
    Pre-configured FSM app that is automatically set at the root of the engine.
    It's the top of the call stack. Its transitions are the ones from the
    transitions file and the default state is the configured one.
    """

    def __new__(cls, *args, **kwargs):
        """
        Generates attributes from the configuration
        """

        cls.transitions = cls._make_transitions()
        cls.default_state = import_class(settings.DEFAULT_STATE)
        return super(RootApp, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def _make_transitions(cls) -> List[Transition]:
        """
        Load the transitions file.
        """

        module_name = settings.TRANSITIONS_MODULE
        module_ = importlib.import_module(module_name)
        return module_.transitions
