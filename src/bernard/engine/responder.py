# coding: utf-8
from typing import TYPE_CHECKING, Union, List
from bernard.layers import Stack, BaseLayer

if TYPE_CHECKING:
    from .platform import Platform
    from .request import Request


Layers = Union[Stack, List[BaseLayer]]


class ResponderError(Exception):
    """
    Base responder exception
    """


class UnacceptableStack(ResponderError):
    """
    The stack you're tryping to send can't be accepted by the platform
    """


class Responder(object):
    """
    The responder is the abstract object that allows to talk back to the
    conversation.

    If you implement a platform, you can overload this class but you probably
    won't need to change anything.
    """

    def __init__(self, platform: 'Platform'):
        self.platform = platform
        self._stacks = []  # type: List[Stack]

    def send(self, stack: Layers):
        """
        Add a message stack to the send list.
        """

        if not isinstance(stack, Stack):
            stack = Stack(stack)

        if not self.platform.accept(stack):
            raise UnacceptableStack('The platform does not allow "{}"'
                                    .format(stack.describe()))

        self._stacks.append(stack)

    def clear(self):
        """
        Reset the send list.
        """

        self._stacks = []

    async def flush(self, request: 'Request'):
        """
        Send all queued messages.

        The first step is to convert all media in the stacked layers then the
        second step is to send all messages as grouped in time as possible.
        """

        for stack in self._stacks:
            await stack.convert_media(self.platform)

        for stack in self._stacks:
            await self.platform.send(request, stack)

    async def make_transition_register(self, request: 'Request'):
        """
        Use all underlying stacks to generate the next transition register.
        """

        register = {}

        for stack in self._stacks:
            register = await stack.patch_register(register, request)

        return register
