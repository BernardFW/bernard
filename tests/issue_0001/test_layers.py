# coding: utf-8
import os

import pytest

import bernard.platforms.facebook.layers as fbl
from bernard import (
    layers,
)
from bernard.conf.utils import (
    patch_conf,
)
from bernard.engine.request import (
    BaseMessage,
    Conversation,
    Request,
    User,
)
from bernard.i18n import (
    intents,
)
from bernard.layers.stack import stack as make_stack
from bernard.storage.register import (
    Register,
)
from bernard.utils import (
    run,
)

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
            'foo': 42,
        }
    })


class MockTextMessage(BaseMessage):
    def get_conversation(self):
        return Conversation('fake_convo')

    def get_layers(self):
        return [
            layers.Text('foo'),
        ]

    def get_platform(self):
        return 'mock'

    def get_user(self):
        return User('fake_user')


# noinspection PyShadowingNames
@pytest.fixture('module')
def text_request(reg):
    req = Request(
        MockTextMessage(),
        reg,
    )
    run(req.transform())
    return req


# noinspection PyShadowingNames
def test_text_layer_patch(text_request):
    l = layers.Text('hello')
    assert run(l.patch_register({}, text_request)) == {}


# noinspection PyShadowingNames
def test_quick_replies_player_patch(text_request):
    l = fbl.QuickRepliesList([
        fbl.QuickRepliesList.TextOption('foo', 'Foo'),
        fbl.QuickRepliesList.TextOption('bar', 'Bar', intents.BAR),
        fbl.QuickRepliesList.LocationOption(),
    ])

    assert run(l.patch_register({}, text_request)) == {
        'choices': {
            'foo': {
                'intent': None,
                'text': 'Foo',
            },
            'bar': {
                'intent': 'BAR',
                'text': 'Bar',
            }
        }
    }


def test_stack():
    l1 = layers.Text('hello')
    l2 = layers.Text('sup?')
    l3 = fbl.QuickRepliesList([
        fbl.QuickRepliesList.TextOption('foo', 'Foo'),
        fbl.QuickRepliesList.TextOption('bar', 'Bar', intents.BAR),
        fbl.QuickRepliesList.LocationOption(),
    ])

    stack = layers.Stack([l1])

    assert stack.has_layer(layers.Text)
    assert not stack.has_layer(fbl.QuickRepliesList)
    assert stack.get_layer(layers.Text) == l1

    with pytest.raises(KeyError):
        assert stack.get_layer(fbl.QuickRepliesList) is None

    stack.layers = [l1, l2, l3]

    assert stack.has_layer(fbl.QuickRepliesList)
    assert stack.get_layer(layers.Text) == l1
    assert stack.get_layers(layers.Text) == [l1, l2]
    assert stack.get_layer(fbl.QuickRepliesList) == l3


# noinspection PyShadowingNames,PyProtectedMember
def test_transform_layers(reg):
    with patch_conf(LOADER_CONFIG):
        req = Request(
            MockTextMessage(),
            reg,
        )
        run(req.transform())
        stack = req.stack

        assert layers.RawText in stack._transformed
        assert stack.get_layer(layers.RawText).text == 'foo'
        assert len(stack.get_layers(layers.Text)) == 1
        assert len(stack.get_layers(layers.RawText)) == 1


def test_match_layer():
    s = make_stack(
        layers.Text('yolo'),
        layers.Text('pouet'),
        fbl.QuickRepliesList([]),
    )

    s.match_exp('(Text|RawText)+ QuickRepliesList?')
