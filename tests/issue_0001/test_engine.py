# coding: utf-8
import pytest
import os
from bernard.engine.request import Request, Conversation, User, BaseMessage
from bernard.storage.register import Register
from bernard import layers as l
from bernard.engine import triggers as trig
from bernard.conf.utils import patch_conf
from bernard.i18n import intents


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


class MockTextMessage(BaseMessage):
    def __init__(self, text, add_qr=False):
        self.text = text
        self.add_qr = add_qr

    def get_conversation(self):
        return Conversation('fake_convo')

    def get_layers(self):
        out = [
            l.Text(self.text),
        ]

        if self.add_qr:
            out += [
                l.QuickReply('foo'),
            ]

        return out

    def get_platform(self):
        return 'mock'

    def get_user(self):
        return User('fake_user')


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
