from bernard.layers import Sleep, stack
from bernard.platforms.telegram.platform import Telegram
from bernard.utils import run
from time import time


def test_telegram_sleep():
    duration = 0.001
    tg = Telegram()
    s = stack(Sleep(duration))

    start = time()
    # noinspection PyTypeChecker
    run(tg.send(None, s))
    stop = time()

    assert (stop - start) >= duration
