# coding: utf-8
import asyncio
import importlib
from typing import List, Tuple, Type, Optional, Text, Iterator
from bernard.conf import settings
from bernard.utils import import_class
from bernard.storage.register import BaseRegisterStore, Register
from .transition import Transition
from .triggers import BaseTrigger
from .state import BaseState
from .request import Request
from .responder import Responder


class FSM(object):
    def __init__(self):
        self.register = self._make_register()
        self.transitions = self._make_transitions()
        self._allowed_states = set(self._make_allowed_states())

    def _make_register(self) -> BaseRegisterStore:
        s = settings.REGISTER_STORE
        store_class = import_class(s['class'])
        return store_class(**s['params'])

    def _make_transitions(self) -> List[Transition]:
        module_name = settings.TRANSITIONS_MODULE
        module_ = importlib.import_module(module_name)
        return module_.transitions

    def _make_allowed_states(self) -> Iterator[Text]:
        for trans in self.transitions:
            yield trans.dest.name()

            if trans.origin:
                yield trans.origin.name()

    async def _find_trigger(self, request: Request) \
            -> Optional[Tuple[
                Optional[BaseTrigger],
                Optional[Type[BaseState]]
            ]]:
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
        origin = request.register.get(Register.STATE)

        if origin in self._allowed_states:
            try:
                return import_class(origin)
            except (AttributeError, ImportError):
                pass

        return import_class(settings.DEFAULT_STATE)
