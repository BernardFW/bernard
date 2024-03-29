import os
from unittest.mock import Mock

import pytest

from bernard import layers as l
from bernard.conf.utils import patch_conf
from bernard.engine import triggers as trig
from bernard.engine.fsm import FSM
from bernard.engine.platform import Platform
from bernard.engine.request import BaseMessage, Conversation, Request, User
from bernard.engine.responder import Responder
from bernard.engine.transition import Transition
from bernard.i18n import intents
from bernard.i18n import translate as t
from bernard.layers.stack import stack
from bernard.platforms.facebook import layers as fbl
from bernard.platforms.test.platform import make_test_fsm
from bernard.storage.register import RedisRegisterStore, Register
from bernard.utils import run

from .states import BaseTestState, Great, Hello, HowAreYou

LOADER_CONFIG = {
    "I18N_TRANSLATION_LOADERS": [
        {
            "loader": "bernard.i18n.loaders.CsvTranslationLoader",
            "params": {
                "file_path": os.path.join(
                    os.path.dirname(__file__),
                    "assets",
                    "trans2.csv",
                ),
            },
        }
    ],
    "I18N_INTENTS_LOADERS": [
        {
            "loader": "bernard.i18n.loaders.CsvIntentsLoader",
            "params": {
                "file_path": os.path.join(
                    os.path.dirname(__file__),
                    "assets",
                    "intents.csv",
                )
            },
        }
    ],
}

ENGINE_SETTINGS_FILE = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "engine_settings.py",
)


@pytest.fixture(scope="module")
def reg():
    return Register(
        {
            Register.TRANSITION: {
                "choices": {
                    "foo": {
                        "text": "Foo",
                        "intent": "FOO",
                    },
                    "bar": {"text": "Some Other Stuff", "intent": "BAR"},
                },
                "foo": 42,
            }
        }
    )


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
            l.Text(self.text),
        ]

        if self.add_qr:
            out += [
                fbl.QuickReply("foo"),
            ]

        return out


class MockChoiceMessage(BaseMockMessage):
    def get_layers(self):
        return [
            fbl.QuickReply("yes"),
            l.Text("yes"),
        ]


class MockEmptyMessage(BaseMockMessage):
    def get_layers(self):
        return []


class MockRequest(Request):
    async def get_locale(self):
        return None


# noinspection PyShadowingNames
@pytest.fixture
def text_request(reg):
    req = MockRequest(
        MockTextMessage("foo"),
        reg,
    )
    run(req.transform())
    return req


# noinspection PyShadowingNames
def test_request_trans_reg(reg):
    req = MockRequest(MockTextMessage("foo"), reg)
    run(req.transform())
    assert req.get_trans_reg("foo") == 42
    assert req.get_trans_reg("bar") is None
    assert req.get_trans_reg("bar", True) is True


# noinspection PyShadowingNames
def test_request_stack(reg):
    req = MockRequest(MockTextMessage("foo"), reg)
    run(req.transform())
    assert req.has_layer(l.Text)
    assert req.get_layer(l.Text).text == "foo"
    assert len(req.get_layers(l.Text)) == 1


# noinspection PyShadowingNames
def test_anything_trigger(text_request):
    with patch_conf(LOADER_CONFIG):
        anything = trig.Anything.builder()
        t = anything(text_request)
        assert t.rank() == 1.0


# noinspection PyShadowingNames
def test_text_trigger(text_request):
    with patch_conf(LOADER_CONFIG):
        tt_factory = trig.Text.builder(intents.BAZ)
        tt = tt_factory(text_request)
        assert run(tt.rank()) == 1.0

        tt_factory = trig.Text.builder(intents.FOO)
        tt = tt_factory(text_request)
        assert run(tt.rank()) == 0.0


# noinspection PyShadowingNames
def test_choice_trigger(reg):
    with patch_conf(LOADER_CONFIG):
        req = MockRequest(MockTextMessage("foo", True), reg)
        run(req.transform())
        ct_factory = trig.Choice.builder()
        ct = ct_factory(req)  # type: trig.Choice
        assert run(ct.rank()) == 1.0
        assert ct.slug == "foo"

        req = MockRequest(MockTextMessage("some other stuff"), reg)
        run(req.transform())
        ct_factory = trig.Choice.builder()
        ct = ct_factory(req)  # type: trig.Choice
        assert run(ct.rank()) == 1.0
        assert ct.slug == "bar"


def test_fsm_init():
    with patch_conf(settings_file=ENGINE_SETTINGS_FILE):
        fsm = FSM()
        assert isinstance(fsm.register, RedisRegisterStore)
        assert isinstance(fsm.transitions, list)

        for t in fsm.transitions:
            assert isinstance(t, Transition)


# noinspection PyShadowingNames,PyProtectedMember
def test_fsm_find_trigger(reg):
    with patch_conf(settings_file=ENGINE_SETTINGS_FILE):
        fsm = FSM()
        run(fsm.async_init())
        req = MockRequest(MockTextMessage("hello"), reg)
        run(req.transform())

        trigger, state, dnr = run(fsm._find_trigger(req))
        assert isinstance(trigger, trig.Text)
        assert state == Hello

        req = MockRequest(MockChoiceMessage(), reg)
        run(req.transform())
        trigger, state, dnr = run(fsm._find_trigger(req))
        assert trigger is None
        assert state is None

        reg = Register(
            {
                Register.STATE: HowAreYou.name(),
                Register.TRANSITION: {
                    "choices": {
                        "yes": {
                            "text": "Yes",
                            "intent": "YES",
                        },
                        "no": {"text": "No", "intent": "NO"},
                    },
                },
            }
        )

        req = MockRequest(MockChoiceMessage(), reg)
        run(req.transform())
        trigger, state, dnr = run(fsm._find_trigger(req))
        assert isinstance(trigger, trig.Choice)
        assert state == Great


# noinspection PyShadowingNames,PyProtectedMember
def test_fsm_confused_state():
    with patch_conf(settings_file=ENGINE_SETTINGS_FILE):
        fsm = FSM()
        run(fsm.async_init())

        reg = Register({})
        req = Request(MockEmptyMessage(), reg)
        run(req.transform())
        assert fsm._confused_state(req) == BaseTestState

        reg = Register({Register.STATE: "tests.issue_0001.states.Hello"})
        req = Request(MockEmptyMessage(), reg)
        run(req.transform())
        assert fsm._confused_state(req) == Hello


# noinspection PyProtectedMember
def test_platform_event():
    platform = Platform()
    mock_cb = Mock()
    data = MockEmptyMessage()
    responder = Responder(platform)

    platform.on_message(mock_cb)
    run(platform._notify(data, responder))

    mock_cb.assert_called_once_with(data, responder, True)


def test_story_hello():
    with patch_conf(settings_file=ENGINE_SETTINGS_FILE):
        _, platform = make_test_fsm()

        platform.handle(
            l.Text("Hello!"),
        )
        platform.assert_state(HowAreYou)
        platform.assert_sent(
            stack(l.Text(t.HELLO)),
            stack(
                l.Text(t.HOW_ARE_YOU),
                fbl.QuickRepliesList(
                    [
                        fbl.QuickRepliesList.TextOption("yes", t.YES, intents.YES),
                        fbl.QuickRepliesList.TextOption("no", t.NO, intents.NO),
                    ]
                ),
            ),
        )

        platform.handle(
            l.Text("Yes"),
            fbl.QuickReply("yes"),
        )
        platform.assert_sent(stack(l.Text(t.GREAT)))
