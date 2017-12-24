import ujson
from typing import Text, Any, Optional, List, Dict
from hashlib import md5

from bernard.engine.request import Request
from bernard.i18n.intents import Intent
from bernard.i18n.translator import TransText, render
from bernard.layers import Stack, Text as TextLayer, Markdown
from bernard.layers.definitions import BaseLayer
from bernard.utils import patch_dict
from ._utils import set_reply_markup


class InlineKeyboardButton(object):
    """
    Represents an inline keyboard button
    """

    def __init__(self, text: TransText):
        """
        See https://core.telegram.org/bots/api#inlinekeyboardmarkup
        """

        self.text = text

    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return {
            'text': await render(self.text, request),
        }

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.text == other.text


class InlineKeyboardUrlButton(InlineKeyboardButton):
    def __init__(self, text: TransText, url: Text):
        super(InlineKeyboardUrlButton, self).__init__(text)
        self.url = url

    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(InlineKeyboardUrlButton, self).serialize(request),
            url=self.url,
        )

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.text == other.text \
               and self.url == other.url


class InlineKeyboardCallbackButton(InlineKeyboardButton):
    def __init__(self, text: TransText, payload: Any):
        super(InlineKeyboardCallbackButton, self).__init__(text)
        self.payload = payload

    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(InlineKeyboardCallbackButton, self).serialize(request),
            callback_data=ujson.dumps(self.payload),
        )

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.text == other.text \
               and self.payload == other.payload


class InlineKeyboardSwitchInlineQueryButton(InlineKeyboardButton):
    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(InlineKeyboardSwitchInlineQueryButton, self)
            .serialize(request),
            switch_inline_query=True,
        )


class InlineKeyboardSwitchInlineQueryCurrentChatButton(InlineKeyboardButton):
    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(InlineKeyboardSwitchInlineQueryCurrentChatButton, self)
            .serialize(request),
            switch_inline_query_current_chat=True,
        )


class InlineKeyboardPayButton(InlineKeyboardButton):
    async def serialize(self, request: Optional[Request] = None) -> Dict:
        return patch_dict(
            await super(InlineKeyboardPayButton, self).serialize(request),
            pay=True,
        )


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
        self.inline_message_id = None

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def _repr_arguments(self):
        return []


class Reply(BaseLayer):
    """
    Add this layer in the the stack in order for the message to be the direct
    reply to the currently analyzed message.
    """

    def __init__(self):
        self.message = None

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


class InlineQuery(BaseLayer):
    def __init__(self, inline_query):
        self.inline_query = inline_query

    @property
    def query(self):
        return self.inline_query['query']

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.inline_query == other.inline_query

    def _repr_arguments(self):
        return [self.query]


class InlineQueryResult(object):
    TYPE = None

    def __init__(self, identifiers: Dict, input_stack: Stack):
        self.identifiers = identifiers
        self.input_stack = input_stack

    @property
    def unique_id(self):
        h = md5()

        for k in sorted(self.identifiers.keys()):
            h.update(f'{k}={self.identifiers[k]}'.encode())

        return h.hexdigest()

    def __eq__(self, other):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    async def serialize(self, request: Optional[Request] = None):
        out = {
            'type': self.TYPE,
            'id': self.unique_id,
        }

        await set_reply_markup(out, request, self.input_stack)

        if self.input_stack.has_layer(TextLayer):
            txt = self.input_stack.get_layer(TextLayer)
            out['input_message_content'] = {
                'message_text': await render(txt.text, request),
            }

        if self.input_stack.has_layer(Markdown):
            txt = self.input_stack.get_layer(Markdown)
            out['input_message_content'] = {
                'message_text': await render(txt.text, request),
                'parse_mode': 'Markdown',
            }

        return out


class InlineQueryResultArticle(InlineQueryResult):
    TYPE = 'article'

    def __init__(self,
                 identifiers: Dict,
                 input_stack: Stack,
                 title: TransText,
                 url: Optional[Text] = None,
                 hide_url: Optional[bool] = None,
                 description: Optional[Text] = None,
                 thumb_url: Optional[Text] = None,
                 thumb_width: Optional[int] = None,
                 thumb_height: Optional[int] = None):
        super(InlineQueryResultArticle, self) \
            .__init__(identifiers, input_stack)

        self.title = title
        self.url = url
        self.hide_url = hide_url
        self.description = description
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    async def serialize(self, request: Optional[Request] = None):
        out = await super(InlineQueryResultArticle, self).serialize(request)

        out['title'] = await render(self.title, request)
        fields = ['url', 'hide_url', 'description', 'thumb_url', 'thumb_width',
                  'thumb_height']

        for field in fields:
            if getattr(self, field) is not None:
                out[field] = getattr(self, field)

        return out

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.identifiers == other.identifiers \
               and self.input_stack == other.input_stack \
               and self.title == other.title \
               and self.url == other.url \
               and self.hide_url == other.hide_url \
               and self.description == other.description \
               and self.thumb_url == other.thumb_url \
               and self.thumb_width == other.thumb_width \
               and self.thumb_height == other.thumb_height

    def __repr__(self):
        return self.title


class AnswerInlineQuery(BaseLayer):
    def __init__(self,
                 results: List[InlineQueryResult],
                 cache_time: Optional[int] = None,
                 is_personal: Optional[bool] = None):
        self.inline_query_id = None
        self.results = results
        self.cache_time = cache_time
        self.is_personal = is_personal

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.inline_query_id == other.inline_query_id \
               and self.results == other.results \
               and self.cache_time == other.cache_time \
               and self.is_personal == other.is_personal

    def _repr_arguments(self):
        return self.results

    async def serialize(self, request: Optional[Request] = None):
        results = []

        for result in self.results:
            results.append(await result.serialize(request))

        out = {
            'inline_query_id': self.inline_query_id,
            'results': results,
        }

        if self.cache_time is not None:
            out['cache_time'] = self.cache_time

        if self.is_personal is not None:
            out['is_personal'] = self.is_personal

        return out


class InlineMessage(BaseLayer):
    """
    This layer indicates that the message is an inline message
    """

    def _repr_arguments(self):
        return []

    def __eq__(self, other):
        return self.__class__ == other.__class__


class BotCommand(BaseLayer):
    """
    That is when the user sends a command to the bot
    """

    def __init__(self, command: Text):
        self.command = command

    def _repr_arguments(self):
        return [self.command]

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.command == other.command
