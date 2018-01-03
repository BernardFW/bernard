import pytest
from bernard import layers as lyr
from bernard.middleware import AutoSleep, MiddlewareManager
from bernard.utils import run


async def alist(it):
    out = []

    async for x in it:
        out.append(x)

    return out


def test_reading_time():
    a = AutoSleep(None)
    text = "J'aime les éléphants"
    assert a.reading_time(text) == pytest.approx(1.9)


# noinspection PyTypeChecker
def test_expand():
    a = AutoSleep(None)

    t = lyr.RawText('hello')
    assert run(alist(a.expand(None, t))) \
        == [lyr.RawText('hello'), lyr.Sleep(0.7)]

    t = lyr.Text('hello')
    assert run(alist(a.expand(None, t))) \
        == [lyr.RawText('hello'), lyr.Sleep(0.7)]

    t = lyr.MultiText('hello')
    assert run(alist(a.expand(None, t))) \
        == [lyr.RawText('hello'), lyr.Sleep(0.7)]

    t = lyr.Sleep(1.0)
    assert run(alist(a.expand(None, t))) == [lyr.Sleep(1.0)]


def test_flush():
    args = []
    kwargs = {}

    async def do_flush(*a, **k):
        args.extend(a)
        kwargs.update(k)

    mm = MiddlewareManager.instance()
    mm.middlewares = [AutoSleep]

    flush = mm.get('flush', do_flush)
    run(flush(None, [lyr.Stack([lyr.Text('hello'), lyr.Text('wassup')])]))

    assert args == [None, [
        lyr.Stack([
            lyr.RawText('hello'),
        ]),
        lyr.Stack([
            lyr.Sleep(0.7),
        ]),
        lyr.Stack([
            lyr.RawText('wassup'),
        ]),
    ]]

    assert kwargs == {}


def test_flush_qr():
    args = []
    kwargs = {}

    async def do_flush(*a, **k):
        args.extend(a)
        kwargs.update(k)

    mm = MiddlewareManager.instance()
    mm.middlewares = [AutoSleep]

    flush = mm.get('flush', do_flush)
    run(flush(None, [
        lyr.Stack([
            lyr.Text('hello'),
            lyr.Text('wassup'),
            lyr.QuickRepliesList([]),
        ]),
    ]))

    assert args == [None, [
        lyr.Stack([
            lyr.RawText('hello'),
        ]),
        lyr.Stack([
            lyr.Sleep(0.7),
        ]),
        lyr.Stack([
            lyr.RawText('wassup'),
            lyr.QuickRepliesList([]),
        ]),
    ]]

    assert kwargs == {}
