# coding: utf-8
from bernard.engine import BaseState
from bernard import layers as lyr
from bernard.i18n import translate as t, intents


class BaseTestState(BaseState):
    async def error(self) -> None:
        self.send(t.ERROR)

    async def handle(self) -> None:
        raise NotImplementedError

    async def confused(self) -> None:
        self.send(t.CONFUSED)


class Hello(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.HELLO))
        self.send(
            lyr.Text(t.HOW_ARE_YOU),
            lyr.QuickRepliesList([
                lyr.QuickRepliesList.TextOption('yes', t.YES, intents.YES),
                lyr.QuickRepliesList.TextOption('no', t.NO, intents.NO),
            ]),
        )


class Great(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.GREAT))


class TooBad(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.TOO_BAD))
