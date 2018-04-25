# coding: utf-8

from bernard.engine import (
    Tr,
    triggers as trg,
)
from bernard.i18n import (
    intents as its,
)

from .states import *

transitions = [
    Tr(
        dest=Hello,
        factory=trg.Text.builder(its.HELLO),
    ),
]
