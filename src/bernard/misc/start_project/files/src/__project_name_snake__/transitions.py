from bernard.engine import Tr
from bernard.engine import triggers as trg
from bernard.i18n import intents as its

from .states import *

transitions = [
    Tr(
        dest=Hello,
        factory=trg.Text.builder(its.HELLO),
    ),
]
