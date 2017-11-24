import ujson
from typing import Text, Any, Optional, List, Dict

from bernard.engine.request import Request
from bernard.i18n.intents import Intent
from bernard.i18n.translator import TransText, render
from bernard.layers.definitions import BaseLayer
from bernard.utils import patch_dict


class InlineKeyboardButton(object):
    """
    Represents an inline keyboard button
    """

    def __init__(
        self,
        text: TransText,
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

    async def serialize(self, request: Optional[Request] = None):
        out = {
            'text': await render(self.text, request),
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
        return self.__class__ == other.__class__ \
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

    async def serialize(self, request: Optional[Request] = None):
        out = []

        for row in self.rows:
            row_ser = []

            for button in row:
                row_ser.append(await button.serialize(request))

            out.append(row_ser)

        return {
            'inline_keyboard': out,
        }

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

    async def serialize(self,
                        callback_query_id: Text,
                        request: Optional[Request] = None) -> Dict:
        out = {
            'callback_query_id': callback_query_id,
        }

        if self.text:
            out['text'] = await render(self.text, request)

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


class KeyboardButton(object):
    def __init__(self,
                 text: TransText,
                 choice: Optional[Text] = None,
                 intent: Optional[Intent] = None) -> None:
        self.text = text
        self.choice = choice
        self.intent = intent
        self._chosen_text = None

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.text == other.text

    async def get_chosen_text(self, request: Optional[Request] = None) -> Text:
        if self._chosen_text is None:
            self._chosen_text = await render(self.text, request)
        return self._chosen_text

    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return {
            'text': await self.get_chosen_text(request),
        }


class ContactKeyboardButton(KeyboardButton):
    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(ContactKeyboardButton, self).serialize(request),
            request_contact=True,
        )


class LocationKeyboardButton(KeyboardButton):
    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(LocationKeyboardButton, self).serialize(request),
            request_location=True,
        )


class ReplyKeyboard(BaseLayer):
    def __init__(
        self,
        keyboard: List[List[KeyboardButton]],
        resize_keyboard: Optional[bool] = None,
        one_time_keyboard: Optional[bool] = None,
        selective: Optional[bool] = None
    ) -> None:
        """
        See https://core.telegram.org/bots/api#replykeyboardmarkup
        """

        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.keyboard == other.keyboard \
               and self.resize_keyboard == other.resize_keyboard \
               and self.one_time_keyboard == other.one_time_keyboard \
               and self.selective == other.selective

    def _repr_arguments(self):
        return [[b.serialize() for b in r] for r in self.keyboard]

    async def serialize(self, request: Optional[Request] = None) -> Dict:
        out = {
            'keyboard': []
        }

        for row in self.keyboard:
            row_ser = []

            for button in row:
                row_ser.append(await button.serialize(request))

            out['keyboard'].append(row_ser)

        if self.resize_keyboard is not None:
            out['resize_keyboard'] = self.resize_keyboard

        if self.one_time_keyboard is not None:
            out['one_time_keyboard'] = self.one_time_keyboard

        if self.selective is not None:
            out['selective'] = self.selective

        return out

    async def patch_register(self, register: Dict, request: 'Request'):
        choices = {}

        for row in self.keyboard:
            for button in row:
                if button.choice:
                    if button.intent:
                        intent = button.intent.key
                    else:
                        intent = None

                    choices[button.choice] = {
                        'intent': intent,
                        'text': await button.get_chosen_text(request),
                    }

        if choices:
            register['choices'] = choices

        return register


class ReplyKeyboardRemove(BaseLayer):
    def __init__(self, selective: Optional[bool] = None):
        self.selective = selective

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.selective == other.selective

    def _repr_arguments(self):
        if self.selective:
            return ['selective']
        else:
            return []

    def serialize(self) -> Dict:
        out = {
            'remove_keyboard': True,
        }

        if self.selective is not None:
            out['selective'] = self.selective

        return out
