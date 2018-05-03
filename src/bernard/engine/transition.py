# coding: utf-8
import asyncio
import logging
from typing import (
    List,
    NamedTuple,
    Optional,
    Text,
    Type,
    Union,
)

from bernard.conf import (
    settings,
)
from bernard.storage.register import (
    Register,
)
from bernard.utils import (
    import_class,
    run_or_return,
)

from .request import (
    Request,
)
from .state import (
    BaseState,
)
from .triggers import (
    BaseTrigger,
)

logger = logging.getLogger('bernard.engine')

Target = Union[Type[BaseState]]


class TransitionRank(NamedTuple):
    """
    Ranking for a given transition as a result of testing it with a given
    request.
    """

    score: float
    trigger: Optional[BaseTrigger]
    dest: Optional[Target]
    dnr: Optional[bool]
    transition_origin: Optional[Target]
    actual_origin: Optional[Target]


class Transition(object):
    """
    Describes a specific transition from one state to the other, with the
    trigger in charge.
    """

    def __init__(self,
                 dest: Type[BaseState],
                 factory,
                 origin: Type[BaseState]=None,
                 weight: float=1.0,
                 desc: Text='',
                 internal: bool=False,
                 do_not_register: bool=False):
        """
        Create the transition.

        :param dest: Destination state
        :param factory: Trigger factory (see `.builder()` on triggers)
        :param origin: Optional origin state
        :param weight: Weight of the transition (1 by default, can be reduced)
        :param desc: A textual description for documentation
        :param internal: That transition is an internal jump (eg it is only
                         triggered right after handling another state).
        :param do_not_register: The transition won't be saved into the
                                register.
        """

        self.origin = origin
        self.dest = dest
        self.factory = factory
        self.weight = weight
        self.desc = desc
        self.internal = internal
        self.do_not_register = do_not_register

        if self.origin:
            self.origin_name = self.origin.name()
        else:
            self.origin_name = None

    def __str__(self):
        return '{} -[{}]-> {}'.format(
            self.origin.__name__ if self.origin else '(init)',
            getattr(self.factory, 'trigger_name', '???'),
            self.dest.__name__,
        )

    async def rank(self, request, origin: Optional[Text]) -> TransitionRank:
        """
        Computes the rank of this transition for a given request.
        """

        if self.origin_name == origin:
            score = 1.0
        elif self.origin_name is None:
            score = settings.JUMPING_TRIGGER_PENALTY
        else:
            return TransitionRank(.0, None, None, None, self.origin, None)

        trigger = self.factory(request)
        rank = await run_or_return(trigger.rank())
        score *= self.weight * (rank or 0.0)

        if origin:
            actual_origin = import_class(origin)
        else:
            actual_origin = None

        return TransitionRank(
            score=score,
            trigger=trigger,
            dest=self.dest,
            dnr=self.do_not_register,
            transition_origin=self.origin,
            actual_origin=actual_origin,
        )


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

        if origin not in self.allowed_states:
            origin = None

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
