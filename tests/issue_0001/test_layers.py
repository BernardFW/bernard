# coding: utf-8
import pytest
from bernard import layers


def test_text_layer_patch():
    l = layers.Text('hello')
    assert l.patch_register({}) == {}


def test_quick_replies_player_patch():
    l = layers.QuickRepliesList([
        layers.QuickRepliesList.TextOption('foo', 'Foo'),
        layers.QuickRepliesList.TextOption('bar', 'Bar', 'BAR'),
        layers.QuickRepliesList.LocationOption(),
    ])

    assert l.patch_register({}) == {
        'choices': {
            'foo': {
                'intents': None,
                'text': {
                    'type': 'string',
                    'value': 'Foo',
                }
            },
            'bar': {
                'intents': 'BAR',
                'text': {
                    'type': 'string',
                    'value': 'Bar',
                }
            }
        }
    }


def test_stack():
    l1 = layers.Text('hello')
    l2 = layers.Text('sup?')
    l3 = layers.QuickRepliesList([
        layers.QuickRepliesList.TextOption('foo', 'Foo'),
        layers.QuickRepliesList.TextOption('bar', 'Bar', 'BAR'),
        layers.QuickRepliesList.LocationOption(),
    ])

    stack = layers.Stack([l1])

    assert stack.has_layer(layers.Text)
    assert not stack.has_layer(layers.QuickRepliesList)
    assert stack.get_layer(layers.Text) == l1

    with pytest.raises(KeyError):
        assert stack.get_layer(layers.QuickRepliesList) is None

    stack.layers = [l1, l2, l3]

    assert stack.has_layer(layers.QuickRepliesList)
    assert stack.get_layer(layers.Text) == l1
    assert stack.get_layers(layers.Text) == [l1, l2]
    assert stack.get_layer(layers.QuickRepliesList) == l3
