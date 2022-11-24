import pytest

from bernard import layers as lyr
from bernard.engine.request import BaseMessage, Conversation, Request, User
from bernard.engine.triggers import Text
from bernard.i18n import intents
from bernard.platforms.facebook import layers as fbl
from bernard.storage.register import Register
from bernard.trigram import Matcher, Trigram
from bernard.utils import run


class BaseMockMessage(BaseMessage):
    def get_platform(self):
        return "mock"

    def get_user(self):
        return User("fake_user")

    def get_conversation(self):
        return Conversation("fake_convo")

    def get_layers(self):
        raise NotImplementedError


class MockTextMessage(BaseMockMessage):
    def __init__(self, text, add_qr=False):
        self.text = text
        self.add_qr = add_qr

    def get_layers(self):
        out = [
            lyr.Text(self.text),
        ]

        if self.add_qr:
            out += [
                fbl.QuickReply("foo"),
            ]

        return out


class MockRequest(Request):
    async def get_locale(self):
        return None


@pytest.fixture(scope="module")
def reg():
    return Register({})


def test_thanks():
    m = Matcher(
        [
            (Trigram("thanks"), Trigram("no thanks"), Trigram("thank you not")),
        ]
    )

    assert m.similarity(Trigram("thanks")) == 1.0
    assert m.similarity(Trigram("no thanks")) == 0.0
    assert m.similarity(Trigram("thank you not")) == 0.0


# noinspection PyShadowingNames
def test_text_trigger(reg):
    intents.db.dict[None] = {
        "THANKS": [("thanks", "no thanks")],
    }

    req = MockRequest(MockTextMessage("no thanks", True), reg)
    run(req.transform())
    ct_factory = Text.builder(intents.THANKS)
    ct: Text = ct_factory(req)

    assert run(ct.rank()) == 0.0
