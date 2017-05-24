# coding: utf-8
import pytest
import os
from unittest.mock import Mock
from bernard.engine.request import Request, Conversation, User, BaseMessage
from bernard.engine.responder import Responder
from bernard.layers.stack import Stack, stack
from bernard.platforms.test.platform import make_test_fsm
from bernard.storage.register import Register
from bernard.storage.register import RedisRegisterStore
from bernard import layers as l
from bernard.engine import triggers as trig
from bernard.engine.fsm import FSM
from bernard.engine.transition import Transition
from bernard.conf.utils import patch_conf
from bernard.i18n import intents, translate as t
from bernard.utils import run
from bernard.engine.platform import Platform
from .states import Hello, Great, BaseTestState


LOADER_CONFIG = {
    'I18N_TRANSLATION_LOADERS': [
        {
            'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
            'params': {
                'file_path': os.path.join(
                    os.path.dirname(__file__),
                    'assets',
                    'trans2.csv',
                ),
            }
        }
    ],
    'I18N_INTENTS_LOADERS': [
        {
            'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
            'params': {
                'file_path': os.path.join(
                    os.path.dirname(__file__),
                    'assets',
                    'intents.csv',
                )
            }
        }
    ],
}

ENGINE_SETTINGS_FILE = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'engine_settings.py',
)


@pytest.fixture('module')
def reg():
    return Register({
        Register.TRANSITION: {
            'choices': {
                'foo': {
                    'text': 'Foo',
                    'intent': 'FOO',
                },
                'bar': {
                    'text': 'Some Other Stuff',
                    'intent': 'BAR'
                },
            },
            'foo': 42,
        }
    })


class BaseMockMessage(BaseMessage):
    def get_platform(self):
        return 'mock'

    def get_user(self):
        return User('fake_user')

    def get_conversation(self):
        return Conversation('fake_convo')

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
                l.QuickReply('foo'),
            ]

        return out


class MockChoiceMessage(BaseMockMessage):
    def get_layers(self):
        return [
            l.QuickReply('yes'),
            l.Text('yes'),
        ]


class MockEmptyMessage(BaseMockMessage):
    def get_layers(self):
        return []


# noinspection PyShadowingNames
@pytest.fixture('module')
def text_request(reg):
    return Request(
        MockTextMessage('foo'),
        reg,
    )


# noinspection PyShadowingNames
def test_request_trans_reg(reg):
    req = Request(MockTextMessage('foo'), reg)
    assert req.get_trans_reg('foo') == 42
    assert req.get_trans_reg('bar') is None
    assert req.get_trans_reg('bar', True) is True


# noinspection PyShadowingNames
def test_request_stack(reg):
    req = Request(MockTextMessage('foo'), reg)
    assert req.has_layer(l.Text)
    assert req.get_layer(l.Text).text == 'foo'
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
        assert tt.rank() == 1.0

        tt_factory = trig.Text.builder(intents.FOO)
        tt = tt_factory(text_request)
        assert tt.rank() == 0.0


# noinspection PyShadowingNames
def test_choice_trigger(reg):
    with patch_conf(LOADER_CONFIG):
        req = Request(MockTextMessage('foo', True), reg)
        ct_factory = trig.Choice.builder()
        ct = ct_factory(req)  # type: trig.Choice
        assert ct.rank() == 1.0
        assert ct.slug == 'foo'

        req = Request(MockTextMessage('some other stuff'), reg)
        ct_factory = trig.Choice.builder()
        ct = ct_factory(req)  # type: trig.Choice
        assert ct.rank() == 1.0
        assert ct.slug == 'bar'


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
        req = Request(MockTextMessage('hello'), reg)

        trigger, state = run(fsm._find_trigger(req))
        assert isinstance(trigger, trig.Text)
        assert state == Hello

        req = Request(MockChoiceMessage(), reg)
        trigger, state = run(fsm._find_trigger(req))
        assert trigger is None
        assert state is None

        reg = Register({
            Register.STATE: Hello.name(),
            Register.TRANSITION: {
                'choices': {
                    'yes': {
                        'text': 'Yes',
                        'intent': 'YES',
                    },
                    'no': {
                        'text': 'No',
                        'intent': 'NO'
                    },
                },
            },
        })

        req = Request(MockChoiceMessage(), reg)
        trigger, state = run(fsm._find_trigger(req))
        assert isinstance(trigger, trig.Choice)
        assert state == Great


# noinspection PyShadowingNames,PyProtectedMember
def test_fsm_confused_state():
    with patch_conf(settings_file=ENGINE_SETTINGS_FILE):
        fsm = FSM()

        reg = Register({})
        req = Request(MockEmptyMessage(), reg)
        assert fsm._confused_state(req) == BaseTestState

        reg = Register({Register.STATE: 'tests.issue_0001.states.Hello'})
        req = Request(MockEmptyMessage(), reg)
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
            l.Text('Hello!'),
        )
        platform.assert_state(Hello)
        platform.assert_sent(
            stack(l.Text(t.HELLO)),
            stack(
                l.Text(t.HOW_ARE_YOU),
                l.QuickRepliesList([
                    l.QuickRepliesList.TextOption('yes', t.YES, intents.YES),
                    l.QuickRepliesList.TextOption('no', t.NO, intents.NO),
                ])
            ),
        )

        platform.handle(
            l.Text('Yes'),
            l.QuickReply('yes'),
        )
        platform.assert_sent(
            stack(l.Text(t.GREAT))
        )
