from bernard.conf.utils import patch_conf
from bernard.engine.request import Request, BaseMessage, User, Conversation
from bernard.i18n import Translator
from bernard.i18n.translator import WordDictionary
from bernard.middleware import BaseMiddleware
from bernard.storage.register import Register
from bernard.utils import run


class AddName(BaseMiddleware):
    async def resolve_trans_params(self, params, request):
        params = await self.next(params, request)
        params['name'] = 'Foo'
        return params

    async def make_trans_flags(self, request):
        flags = await self.next(request)
        flags['gender'] = 'male'
        return flags


CONFIG = {
    'MIDDLEWARES': [
        'tests.issue_0030.test_hooks.AddName',
    ],
}


# noinspection PyAbstractClass
class MockUser(User):
    async def get_timezone(self):
        return None

    async def get_locale(self):
        return None


class BaseMockMessage(BaseMessage):
    def get_platform(self):
        return 'mock'

    def get_user(self):
        return MockUser('fake_user')

    def get_conversation(self):
        return Conversation('fake_convo')

    def get_layers(self):
        raise NotImplementedError


class MockEmptyMessage(BaseMockMessage):
    def get_layers(self):
        return []


def test_resolve_params():
    with patch_conf(CONFIG):
        wd = WordDictionary()
        t = Translator(wd)

        wd.update_lang(None, [
            ('HELLO', 'Hello, {name}!'),
        ], {})

        assert run(t.HELLO.render_list(None)) == ['Hello, Foo!']


def test_make_trans_flags():
    with patch_conf(CONFIG):
        wd = WordDictionary()
        t = Translator(wd)

        req = Request(
            MockEmptyMessage(),
            Register({}),
        )

        wd.update_lang(None, [
            ('HELLO', 'Hello boy'),
        ], {'gender': 'male'})

        wd.update_lang(None, [
            ('HELLO', 'Hello girl'),
        ], {'gender': 'female'})

        assert run(t.HELLO.render_list(req)) == ['Hello boy']
