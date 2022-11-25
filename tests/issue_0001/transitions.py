from bernard.engine import Tr, triggers
from bernard.i18n import intents

from .states import Great, Hello, HowAreYou, TooBad

# noinspection PyTypeChecker
transitions = [
    Tr(Hello, triggers.Text.builder(intents.HELLO)),
    Tr(HowAreYou, triggers.Anything.builder(), Hello, internal=True),
    Tr(Great, triggers.Choice.builder(when="yes"), HowAreYou),
    Tr(TooBad, triggers.Choice.builder(when="no"), HowAreYou),
]
