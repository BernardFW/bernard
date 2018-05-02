# coding: utf-8
import asyncio
import logging
from typing import (
    List,
    NamedTuple,
    Optional,
    Text,
    Type,
)

from bernard.conf import (
    settings,
)
from bernard.engine import (
    BaseState,
)
from bernard.engine.request import (
    Request,
)
from bernard.engine.transition import (
    Target,
    Transition,
    TransitionRank,
)
from bernard.engine.triggers import (
    BaseTrigger,
)
from bernard.storage.register import (
    Register,
)
from bernard.utils import (
    import_class,
)

logger = logging.getLogger('bernard.engine')


class UpcomingState(NamedTuple):
    """
    When transitions have been selected, this is emitted to know what to run
    next with all the meta-information that will be used as arguments, for
    logging, and so on.
    """

    state: Optional[Target]
    trigger: Optional[BaseTrigger]
    dnr: Optional[bool]
    score: Optional[float]
    transition_origin: Optional[Target]
    actual_origin: Optional[Target]


class TransitionManager(object):
    """
    Transition-finding engine. It knows nothing but the transitions, the
    current state and the request.
    """

    def __init__(self,
                 transitions: List[Transition],
                 default_state: Type[BaseState]):
        """
        Constructor, should run once when creating the app.

        :param transitions: A list of transitions to consider
        :param default_state: The state to default to when things go south
        """

        self.transitions = transitions
        self.default_state = default_state
        self.allowed_states = set(self._make_allowed_states())

    def _make_allowed_states(self):
        """
        Generates a list of allowed states in order to check that the register
        makes sense when receiving a request.
        """

        for trans in self.transitions:
            yield trans.dest.name()

            if trans.origin:
                yield trans.origin.name()

    def confused_state(self, request: Request) -> Type[BaseState]:
        """
        For the current request, try to find the state onto which call the
        `confused()` method. If there is a current state then it's the one
        that is chosen, but otherwise it falls back to the default state.
        """

        origin = request.register.get()

        if origin in self.allowed_states:
            try:
                cls: Type[BaseState] = import_class(origin)
                return cls
            except (AttributeError, ImportError):
                pass

        return self.default_state

    async def find_trigger(self,
                           request: Request,
                           origin: Optional[Text] = None,
                           internal: bool = False) -> TransitionRank:
        """
        Find the best trigger for this request, or go away.

        :param request: Request to handle
        :param origin: Force a different origin from the one of the request,
                       used in case of internal transitions.
        :param internal: Is this transition internal?
        """

        reg = request.register

        if not origin:
            origin = reg.get(Register.STATE)

        results: List[TransitionRank] = await asyncio.gather(*(
            x.rank(request, origin)
            for x
            in self.transitions
            if x.internal == internal
        ))

        if len(results):
            rank = max(results, key=lambda x: x.score)

            if rank.score >= settings.MINIMAL_TRIGGER_SCORE:
                return rank

        return TransitionRank(0.0, None, None, None, None, None)

    async def build_upcoming(self, request: Request) -> UpcomingState:
        """
        Build the upcoming state for the request by finding the right trigger
        and defining the state to call.

        The state is guaranteed to be set, however if no transitions were
        triggered, the returned trigger will be `None` and the engine is
        expected to call `confused()` instead of `handle()`.
        """

        rank = await self.find_trigger(request)
        state_class = rank.dest

        if rank.trigger is None:
            if not request.message.should_confuse():
                return UpcomingState(None, None, None, .0, None, None)

            state_class = self.confused_state(request)

        return UpcomingState(
            state_class,
            rank.trigger,
            rank.dnr,
            rank.score,
            rank.transition_origin,
            rank.actual_origin,
        )
