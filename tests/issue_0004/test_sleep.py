from time import time

from bernard.layers import Sleep, stack
from bernard.platforms.facebook.platform import Facebook
from bernard.utils import run


def test_facebook_sleep():
    duration = 0.001
    fb = Facebook()
    s = stack(Sleep(duration))

    start = time()
    # noinspection PyTypeChecker
    run(fb.send(None, s))
    stop = time()

    assert (stop - start) >= duration
