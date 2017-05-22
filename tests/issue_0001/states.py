# coding: utf-8
from bernard.engine import BaseState


class TestBaseState(BaseState):
    async def error(self) -> None:
        pass

    async def handle(self) -> None:
        raise NotImplementedError

    async def confused(self) -> None:
        pass


class Hello(TestBaseState):
    async def handle(self):
        pass


class Great(TestBaseState):
    async def handle(self):
        pass


class TooBad(TestBaseState):
    async def handle(self):
        pass
