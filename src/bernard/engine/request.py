# coding: utf-8
from typing import Text, Any, List, Type, Optional, TYPE_CHECKING
from datetime import tzinfo
from enum import Enum
from bernard.storage.register import Register
from bernard.layers import BaseLayer, Stack
from bernard.layers.stack import L


if TYPE_CHECKING:
    from bernard.i18n.translator import Flags


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

    class Gender(Enum):
        """
        Represents the gender of a person. Unknown is to be used either when
        you actually don't know or when the gender is more complex than male or
        female.
        """

        male = 'male'
        female = 'female'
        unknown = 'unknown'

    def __init__(self, id_):
        self.id = id_

    async def get_gender(self) -> Gender:
        """
        Returns the gender of the person if known
        """
        return self.Gender.unknown

    async def get_friendly_name(self) -> Text:
        """
        Computes a friendly name (like in "Hi Rémy")
        """
        raise NotImplementedError

    async def get_formal_name(self) -> Text:
        """
        Computes a formal name (like in "Howdy Mr Sanchez")
        """
        raise NotImplementedError

    async def get_full_name(self) -> Text:
        """
        Computes an administrative full name (like "Name: Rémy Sanchez")
        """
        raise NotImplementedError

    async def get_timezone(self) -> Optional[tzinfo]:
        """
        Return the current time zone of the user
        """
        raise NotImplementedError

    async def get_locale(self) -> Text:
        """
        Returns a locale-descripting string
        """
        raise NotImplementedError

    async def get_postback_url(self) -> Text:
        """
        Returns a URL which can be POSTed to. The POST body must be a JSON
        message that will be used as payload for a synthetic postback layer
        from this user.
        """
        raise NotImplementedError


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

    def should_confuse(self) -> bool:
        """
        If this returns "True" then the message should trigger a confused state
        when not understood.

        Otherwise, it is simply ignored.
        """

        return True


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
        self.custom_content = {}

        self._locale_override = None

    async def transform(self):
        await self.stack.transform(self)

    def get_trans_reg(self, name: Text, default: Any=None) -> Any:
        """
        Convenience function to access the transition register of a specific
        kind.

        :param name: Name of the register you want to see
        :param default: What to return by default
        """

        tr = self.register.get(Register.TRANSITION, {})
        return tr.get(name, default)

    def has_layer(self, class_: Type[L], became: bool=True) -> bool:
        """
        Proxy to stack
        """
        return self.stack.has_layer(class_, became)

    def get_layer(self, class_: Type[L], became: bool=True) -> L:
        """
        Proxy to stack
        """
        return self.stack.get_layer(class_, became)

    def get_layers(self, class_: Type[L], became: bool=True) -> List[L]:
        """
        Proxy to stack
        """
        return self.stack.get_layers(class_, became)

    def set_locale_override(self, locale: Text) -> None:
        """
        This allows to override manually the locale that will be used in
        replies.

        :param locale: Name of the locale (format 'fr' or 'fr_FR')
        """

        self._locale_override = locale

    async def get_locale(self) -> Text:
        """
        Get the locale to use for this request. It's either the overriden locale
        or the locale provided by the platform.

        :return: Locale to use for this request
        """

        if self._locale_override:
            return self._locale_override
        else:
            return await self.user.get_locale()

    async def get_trans_flags(self) -> 'Flags':
        """
        Gives a chance to middlewares to make the translation flags
        """

        from bernard.middleware import MiddlewareManager

        async def make_flags(request: Request) -> 'Flags':
            return {}

        mf = MiddlewareManager.instance().get('make_trans_flags', make_flags)
        return await mf(self)
