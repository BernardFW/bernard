# coding: utf-8
from typing import Optional
from bernard.engine.triggers import BaseTrigger
from bernard.layers import BaseLayer, Text
from .responder import Responder
from .request import Request


class BaseState(object):
    """
    This is the base state interface. When implementing a bot, you need to
    implement it.

    What is advised is to create your own base class for your bot, so it can
    have a default `error()` and `confused()` behaviour, and then inherit
    this class from everywhere. This base subclass can then become the
    `DEFAULT_STATE` in the configuration.
    """

    def __init__(self,
                 request: Request,
                 responder: Responder,
                 trigger: Optional[BaseTrigger]=None):
        self.request = request
        self.responder = responder
        self.trigger = trigger

    @classmethod
    def name(cls):
        """
        Generate a unique name for this state based on its fully qualified
        name.
        """

        return '{}.{}'.format(
            cls.__module__,
            cls.__qualname__,
        )

    async def error(self) -> None:
        """
        This is what happens when the code screws up (aka error 500).
        """

        raise NotImplementedError

    async def confused(self) -> None:
        """
        This is called when a good state cannot be found.
        """

        raise NotImplementedError

    async def handle(self) -> None:
        """
        That's the regular state handling method that gets called when all
        goes well. You need to overload this one and reply your things to the
        user.
        """

        raise NotImplementedError

    def send(self, *stack: BaseLayer):
        """
        Shortcut method to send a reply.
        """

        self.responder.send(list(stack))


class DefaultState(BaseState):
    """
    That's the default default state. You really need to make your own default
    state but this one here is created so not everything crashes if you forget
    to.
    """

    def handle(self) -> None:
        """
        Let's not handle things.
        """
        raise NotImplementedError

    def confused(self) -> None:
        """
        Send a stupid text.
        """
        self.send(Text('I do not understand this text'))

    def error(self) -> None:
        """
        Send another stupid text.
        """
        self.send(Text('Something went wrong in my head and I cannot answer'))

