# coding: utf-8


class BaseState(object):
    def __init__(self, request, responder):
        self.request = request
        self.responder = responder

    @classmethod
    def name(cls):
        return '{}.{}'.format(
            cls.__module__,
            cls.__qualname__,
        )

    async def error(self) -> None:
        raise NotImplementedError

    async def confused(self) -> None:
        raise NotImplementedError

    async def handle(self) -> None:
        raise NotImplementedError


class DefaultState(BaseState):
    def handle(self) -> None:
        raise NotImplementedError

    def confused(self) -> None:
        raise NotImplementedError

    def error(self) -> None:
        raise NotImplementedError

