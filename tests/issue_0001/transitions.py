# coding: utf-8

from bernard.engine import Tr, triggers
from bernard.i18n import intents
from .states import Hello, Great, TooBad

# noinspection PyTypeChecker
transitions = [
    Tr(Hello, triggers.Text.builder(intents.HELLO)),
    Tr(Great, triggers.Choice.builder(when='yes'), Hello),
    Tr(TooBad, triggers.Choice.builder(when='no'), Hello),
]
