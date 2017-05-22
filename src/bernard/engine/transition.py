# coding: utf-8
from typing import Text, Optional, Tuple, Type
from bernard.conf import settings
from bernard.utils import run_or_return
from .triggers import BaseTrigger
from .state import BaseState


class Transition(object):
    def __init__(self,
                 dest: Type[BaseState],
                 factory,
                 origin: Type[BaseState]=None,
                 weight: float=1.0,
                 desc: Text=''):
        self.origin = origin
        self.dest = dest
        self.factory = factory
        self.weight = weight
        self.desc = desc

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
        if self.origin_name == origin:
            score = 1.0
        elif self.origin_name is None:
            score = settings.JUMPING_TRIGGER_PENALTY
        else:
            return 0.0, None, None

        trigger = self.factory(request)
        score *= self.weight * (await run_or_return(trigger.rank()) or 0.0)

        return score, trigger, self.dest
