# coding: utf-8
import pytest
from bernard.engine.request import Request, Conversation, User, BaseMessage
from bernard.storage.register import Register
from bernard import layers as l


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
            l.Text('foo'),
        ]

    def get_platform(self):
        return 'mock'

    def get_user(self):
        return User('fake_user')


# noinspection PyShadowingNames
def test_request_trans_reg(reg):
    req = Request(MockTextMessage(), reg)
    assert req.get_trans_reg('foo') == 42
    assert req.get_trans_reg('bar') is None
    assert req.get_trans_reg('bar', True) is True


# noinspection PyShadowingNames
def test_request_stack(reg):
    req = Request(MockTextMessage(), reg)
    assert req.has_layer(l.Text)
    assert req.get_layer(l.Text).text == 'foo'
    assert len(req.get_layers(l.Text)) == 1
