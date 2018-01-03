import pytest

from bernard.conf.utils import patch_conf
from bernard.middleware import BaseMiddleware, MiddlewareManager
from bernard.utils import run


class IsNotMiddleware(object):
    pass


class AddOne(BaseMiddleware):
    async def return_n(self, n):
        return (await self.next(n)) + 1


class BadPlayer(BaseMiddleware):
    async def return_n(self, n):
        return n


class DoNothing(BaseMiddleware):
    pass


async def return_n(n):
    return n


def test_caller_stack():
    m = MiddlewareManager()
    m.middlewares = [
        AddOne,
        AddOne,
    ]

    rn = m.get('return_n', return_n)

    assert run(rn(40)) == 42


def test_caller_extra():
    m = MiddlewareManager()

    rn = m.get('return_n', return_n)

    assert run(rn(0)) == 0

    with pytest.raises(ValueError):
        run(rn(0))


def test_build_stack():
    m = MiddlewareManager()
    m.middlewares = [
        AddOne,
        DoNothing,
    ]
    rn = m.get('return_n', return_n)

    # noinspection PyProtectedMember,PyUnresolvedReferences
    assert len(rn._stack) == 1


def test_health_check():
    with patch_conf({'MIDDLEWARES': None}):
        assert len(list(MiddlewareManager.health_check())) == 1

    with patch_conf({'MIDDLEWARES': ['does.not.Exist']}):
        assert len(list(MiddlewareManager.health_check())) == 1

    conf = {'MIDDLEWARES': ['tests.issue_0029.test_manager.IsNotMiddleware']}
    with patch_conf(conf):
        assert len(list(MiddlewareManager.health_check())) == 1

    conf = {'MIDDLEWARES': ['tests.issue_0029.test_manager.AddOne']}
    with patch_conf(conf):
        assert len(list(MiddlewareManager.health_check())) == 0


def test_init():
    conf = {'MIDDLEWARES': ['tests.issue_0029.test_manager.AddOne']}
    with patch_conf(conf):
        m = MiddlewareManager()
        m.init()

        assert m.middlewares == [AddOne]


# noinspection PyProtectedMember
def test_instance():
    MiddlewareManager._instance = None

    i1 = MiddlewareManager.instance()
    i2 = MiddlewareManager.instance()
    assert i1 is i2

    MiddlewareManager._instance = None


def test_next_not_called():
    m = MiddlewareManager()
    m.middlewares = [BadPlayer]

    rn = m.get('return_n', return_n)

    error_msg = '"BadPlayer.return_n" did not call `self.next()`, or forgot ' \
                'to await it'

    with pytest.raises(TypeError) as exec_info:
        run(rn(0))

    assert str(exec_info.value) == error_msg
