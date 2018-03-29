from bernard import layers as lyr
from bernard.middleware import (
    AutoType,
    MiddlewareManager,
)
from bernard.utils import (
    run,
)


def test_flush():
    args = []
    kwargs = {}

    async def do_flush(*a, **k):
        args.extend(a)
        kwargs.update(k)

    mm = MiddlewareManager.instance()
    mm.middlewares = [AutoType]

    flush = mm.get('flush', do_flush)
    run(flush(None, [
        lyr.Stack([lyr.Text('hello')]),
        lyr.Stack([lyr.Text('wassup')]),
    ]))

    assert args == [None, [
        lyr.Stack([
            lyr.Text('hello'),
        ]),
        lyr.Stack([
            lyr.Typing(),
        ]),
        lyr.Stack([
            lyr.Text('wassup'),
        ]),
        lyr.Stack([
            lyr.Typing(False),
        ]),
    ]]

    assert kwargs == {}


def test_typify():
    at = AutoType(None)
    assert at.typify(lyr.stack(lyr.Typing())) == [lyr.stack(lyr.Typing())]
