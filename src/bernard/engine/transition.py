# coding: utf-8
from typing import Text, Optional, Tuple, Type
from bernard.conf import settings
from bernard.utils import run_or_return
from .triggers import BaseTrigger
from .state import BaseState


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
                 internal: bool=False):
        """
        Create the transition.

        :param dest: Destination state
        :param factory: Trigger factory (see `.builder()` on triggers)
        :param origin: Optional origin state
        :param weight: Weight of the transition (1 by default, can be reduced)
        :param desc: A textual description for documentation
        :param internal: That transition is an internal jump (eg it is only
                         triggered right after handling another state).
        """

        self.origin = origin
        self.dest = dest
        self.factory = factory
        self.weight = weight
        self.desc = desc
        self.internal = internal

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

    async def rank(self, request, origin: Optional[Text]) \
            -> Tuple[float, Optional[BaseTrigger], Optional[type]]:
        """
        Computes the rank of this transition for a given request.

        It returns (in order):

            - The score (from 0 to 1)
            - The trigger instance (if it matched)
            - The class of the destination state (if matched)
        """

        if self.origin_name == origin:
            score = 1.0
        elif self.origin_name is None:
            score = settings.JUMPING_TRIGGER_PENALTY
        else:
            return 0.0, None, None

        trigger = self.factory(request)
        rank = await run_or_return(trigger.rank())
        score *= self.weight * (rank or 0.0)

        return score, trigger, self.dest
