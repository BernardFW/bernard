# coding: utf-8
from datetime import datetime
from typing import List
from bernard.engine import BaseState
from bernard import layers as lyr
from bernard.platforms.telegram import layers as tgr
from bernard.i18n import translate as t, intents


class BaseTestState(BaseState):
    async def error(self) -> None:
        """Triggered when there is an internal error"""
        self.send(lyr.Text(t.ERROR))

    async def confused(self) -> None:
        """Triggered when the bot does not understand what the user says"""
        self.send(lyr.Text(t.CONFUSED))

    async def handle(self) -> None:
        raise NotImplementedError


class Text(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.TEXT))
        self.send(lyr.Text('Some other text'))


class Locale(BaseTestState):
    async def handle(self):
        locale = await self.request.user.get_locale()

        self.send(lyr.Text(t('LOCALE', locale=locale)))


class Keyboard(BaseTestState):
    async def handle(self):
        stack: List[lyr.BaseLayer] = [
            lyr.Text(t('KEYBOARD', now=datetime.now())),
            tgr.InlineKeyboard([
                [
                    tgr.InlineKeyboardButton(
                        text='Notif',
                        callback_data={
                            'action': 'notif'
                        },
                    ),
                    tgr.InlineKeyboardButton(
                        text='Alert',
                        callback_data={
                            'action': 'alert'
                        },
                    ),
                ],
            ])
        ]

        if self.request.has_layer(lyr.Postback):
            pb = self.request.get_layer(lyr.Postback)
            action = pb.payload['action']

            stack.append(tgr.Update())

            if action == 'notif':
                stack.append(
                    tgr.AnswerCallbackQuery('This is a notification'),
                )
            elif action == 'alert':
                stack.append(
                    tgr.AnswerCallbackQuery(
                        'This is a notification',
                        show_alert=True,
                    ),
                )

        self.send(*stack)
