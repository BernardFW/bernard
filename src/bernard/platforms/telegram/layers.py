import ujson
from typing import Text, Any, Optional, List
from bernard.layers.definitions import BaseLayer


class InlineKeyboardButton(object):
    """
    Represents an inline keyboard button
    """

    def __init__(
        self,
        text: Text,
        url: Optional[Text] = None,
        callback_data: Optional[Any] = None,
        switch_inline_query: Optional[Text] = None,
        switch_inline_query_current_chat: Optional[Text] = None,
        pay: Optional[bool] = None,
    ):
        """
        See https://core.telegram.org/bots/api#inlinekeyboardmarkup
        """

        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = \
            switch_inline_query_current_chat
        self.pay = pay

    def serialize(self):
        out = {
            'text': self.text,
        }

        if self.url:
            out['url'] = self.url

        if self.callback_data:
            out['callback_data'] = ujson.dumps(self.callback_data)

        if self.switch_inline_query:
            out['switch_inline_query'] = self.switch_inline_query

        if self.switch_inline_query_current_chat:
            out['switch_inline_query_current_chat'] = \
                self.switch_inline_query_current_chat

        if self.pay is not None:
            out['pay'] = self.pay

        return out

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        return self.__class__ == other.__class__  \
            and self.text == other.text \
            and self.url == other.url \
            and self.callback_data == other.callback_data \
            and self.switch_inline_query == other.switch_inline_query \
            and self.switch_inline_query_current_chat == \
            other.switch_inline_query_current_chat \
            and self.pay == other.pay


class InlineKeyboard(BaseLayer):
    def __init__(self, rows: List[List[InlineKeyboardButton]]):
        self.rows = rows

    def serialize(self):
        return [[b.serialize() for b in r] for r in self.rows]

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.rows == other.rows

    def _repr_arguments(self):
        return self.rows


class AnswerCallbackQuery(BaseLayer):
    """
    Use this layer to answer callback queries. The platform will automatically
    generate an empty AnswerCallbackQuery when a callback query is sent, but
    if you place one in the answer then it will be sent in place of the default
    one.
    """

    def __init__(
        self,
        text: Optional[Text] = None,
        show_alert: Optional[bool] = None,
        url: Optional[Text] = None,
        cache_time: Optional[int] = None,
    ):
        self.text = text
        self.show_alert = show_alert
        self.url = url
        self.cache_time = cache_time

    def serialize(self, callback_query_id):
        out = {
            'callback_query_id': callback_query_id,
        }

        if self.text:
            out['text'] = self.text

        if self.show_alert is not None:
            out['show_alert'] = self.show_alert

        if self.url:
            out['url'] = self.url

        if self.cache_time is not None:
            out['cache_time'] = self.cache_time

        return out

    def __eq__(self, other):
        return self.__class__ == other.__class \
            and self.text == other.text \
            and self.show_alert == other.show_alert \
            and self.url == other.url \
            and self.cache_time == other.cache_time

    def _repr_arguments(self):
        return [self.text]


class Update(BaseLayer):
    """
    Add this layer in the stack if you want to update a previous text message.
    Only one text message can be updated at once so please make sure that your
    stack has only one text message (unless you want some unexpected
    behaviour).
    """

    def __init__(self):
        self.message_id = None
        self.chat_id = None

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def _repr_arguments(self):
        return []
