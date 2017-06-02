# coding: utf-8
from typing import List, Tuple, Type
from bernard.engine.platform import Platform
from bernard.engine.request import BaseMessage, User, Conversation, Request
from bernard.engine.responder import Responder
from bernard.engine.state import BaseState
from bernard.layers import Stack, BaseLayer
from bernard.engine.fsm import FSM
from bernard.storage.register import Register
from bernard.utils import run


class TestUser(User):
    """
    Mock user object
    """

    async def get_timezone(self):
        return None


class TestConversation(Conversation):
    """
    Mock conversation object.
    """


class TestMessage(BaseMessage):
    """
    Mock message (with arbitrary content)
    """

    def __init__(self, stack: Stack):
        self.stack = stack

    def get_platform(self):
        """
        That's the test platform
        """
        return 'test'

    def get_user(self):
        """
        So far the user is static
        """
        return TestUser('test:test-id')

    def get_conversation(self):
        """
        So far the conversation is static
        """
        return TestConversation('test:test-id')

    def get_layers(self):
        """
        We'll return the layers set at init time.
        """
        return self.stack.layers


class TestResponder(Responder):
    """
    It's just a proxy to the platform's `send()` method.
    """


class TestPlatform(Platform):
    """
    This is a platform especially design for unit testing. You can create it
    using the `make_test_fsm()` method below.

    The usage is pretty simple:

    >>> from bernard import layers as l
    >>> from bernard.i18n import translate as t
    >>> from tests.issue_0001.states import Hello
    >>> _, platform = make_test_fsm()
    >>> platform.handle(l.Text('Hello!'))
    >>> platform.assert_state(Hello)
    >>> platform.assert_sent(l.stack(l.Text(t.HELLO)))
    """

    fsm_creates_task = False

    def __init__(self):
        super(TestPlatform, self).__init__()
        self.sent = []  # type: List[Stack]

    async def send(self, request: Request, stack: Stack):
        """
        Store the message to be sent for later analysis
        """
        self.sent.append(stack)

    def accept(self, stack: Stack):
        """
        So far we accept anything, it's up to the test to test that things sent
        are the right ones.
        """
        return True

    def handle(self, *layers: BaseLayer):
        """
        Call this method to send a test message. Call it OUTSIDE the async
        loop. It will return when the message is fully handled.
        """

        self.sent = []
        stack = Stack(list(layers))
        message = TestMessage(stack)
        responder = TestResponder(self)

        run(self._notify(message, responder))

    def assert_sent(self, *stacks: Stack):
        """
        Assert that the sent stacks are identical to the ones provided as
        argument here.
        """

        assert len(stacks) == len(self.sent)

        for s1, s2 in zip(stacks, self.sent):
            assert s1 == s2

    def assert_state(self, state_class: Type[BaseState]):
        """
        Assert that the state returned in the register is the one passed as
        argument.
        """

        assert self._register
        assert Register.STATE in self._register
        assert self._register[Register.STATE] == state_class.name()


def make_test_fsm() -> Tuple[FSM, TestPlatform]:
    """
    Generate both a FSM and a test platform for unit testing purposes.

    The will use the current configuration to load stories and transitions.
    """

    fsm = FSM()
    run(fsm.async_init())

    platform = TestPlatform()
    # noinspection PyTypeChecker
    platform.on_message(fsm.handle_message)

    return fsm, platform
