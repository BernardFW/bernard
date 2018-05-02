# coding: utf-8
from typing import (
    NamedTuple,
    Optional,
    Text,
    Type,
    Union,
)

from bernard.conf import (
    settings,
)
from bernard.utils import (
    import_class,
    run_or_return,
)

from .state import (
    BaseState,
)
from .triggers import (
    BaseTrigger,
)

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
