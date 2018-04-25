# coding: utf-8

from bernard.engine import (
    Tr,
    triggers as trg,
)
from bernard.i18n import (
    intents as its,
)

from .states import *
from .triggers import *

transitions = [
    Tr(
        dest=S001xWelcome,
        factory=trg.Action.builder('get_started'),
    ),
    Tr(
        dest=S002xGuessANumber,
        factory=trg.Action.builder('guess'),
    ),
    Tr(
        dest=S002xGuessANumber,
        origin=S001xWelcome,
        factory=trg.Choice.builder('play'),
    ),
    Tr(
        dest=S003xGuessAgain,
        origin=S002xGuessANumber,
        factory=Number.builder(is_right=False),
    ),
    Tr(
        dest=S003xGuessAgain,
        origin=S003xGuessAgain,
        factory=Number.builder(is_right=False),
    ),
    Tr(
        dest=S004xCongrats,
        origin=S003xGuessAgain,
        factory=Number.builder(is_right=True),
    ),
    Tr(
        dest=S004xCongrats,
        origin=S002xGuessANumber,
        factory=Number.builder(is_right=True),
    ),
    Tr(
        dest=S002xGuessANumber,
        origin=S004xCongrats,
        factory=trg.Choice.builder('again'),
    ),
]
