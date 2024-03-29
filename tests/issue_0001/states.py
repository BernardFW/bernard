from bernard import layers as lyr
from bernard.engine import BaseState
from bernard.i18n import intents
from bernard.i18n import translate as t
from bernard.platforms.facebook import layers as fbl


class BaseTestState(BaseState):
    async def error(self) -> None:
        self.send(lyr.Text(t.ERROR))

    async def handle(self) -> None:
        raise NotImplementedError

    async def confused(self) -> None:
        self.send(lyr.Text(t.CONFUSED))


class Hello(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.HELLO))


class HowAreYou(BaseTestState):
    async def handle(self):
        self.send(
            lyr.Text(t.HOW_ARE_YOU),
            fbl.QuickRepliesList(
                [
                    fbl.QuickRepliesList.TextOption("yes", t.YES, intents.YES),
                    fbl.QuickRepliesList.TextOption("no", t.NO, intents.NO),
                ]
            ),
        )


class Great(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.GREAT))


class TooBad(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.TOO_BAD))
