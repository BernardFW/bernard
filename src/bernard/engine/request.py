# coding: utf-8
from typing import Text, Any, List
from bernard.storage.register import Register
from bernard.layers import BaseLayer, Stack
from bernard.layers.stack import L


class Conversation(object):
    """
    Abstract representation of a conversation.
    """
    def __init__(self, id_):
        self.id = id_


class User(object):
    """
    Abstract representation of a user.
    """
    def __init__(self, id_):
        self.id = id_


class BaseMessage(object):
    """
    This class represents a message received by the platform. It is in charge
    of implementing the following abstract methods from what the platform
    can provide.

    The methods here should, in principle, only get called once. Though it's
    not guaranteed.
    """

    def get_platform(self) -> Text:
        """
        Return a static string indicating the name of the platform that this
        message comes from.
        """
        raise NotImplementedError

    def get_user(self) -> User:
        """
        Return a user object.
        """
        raise NotImplementedError

    def get_conversation(self) -> Conversation:
        """
        Return a conversation object.
        """
        raise NotImplementedError

    def get_layers(self) -> List[BaseLayer]:
        """
        Return the layers found in the message.
        """
        raise NotImplementedError


class Request(object):
    """
    The request object is generated after each message. Its goal is to provide
    a comprehensive access to the received message and its context to be used
    by the transitions and the handlers.
    """

    def __init__(self,
                 message: BaseMessage,
                 register: Register):
        self.message = message
        self.platform = message.get_platform()
        self.conversation = message.get_conversation()
        self.user = message.get_user()
        self.stack = Stack(message.get_layers())
        self.register = register

    def get_trans_reg(self, name: Text, default: Any=None) -> Any:
        """
        Convenience function to access the transition register of a specific
        kind.

        :param name: Name of the register you want to see
        :param default: What to return by default
        """

        tr = self.register.get(Register.TRANSITION, {})
        return tr.get(name, default)

    def has_layer(self, class_: L) -> bool:
        """
        Proxy to stack
        """
        return self.stack.has_layer(class_)

    def get_layer(self, class_: L) -> L:
        """
        Proxy to stack
        """
        return self.stack.get_layer(class_)

    def get_layers(self, class_: L) -> List[L]:
        """
        Proxy to stack
        """
        return self.stack.get_layers(class_)
