# coding: utf-8

from bernard.engine import Tr, triggers
from bernard.i18n import intents
from .states import Text, Keyboard, Locale

transitions = [
    Tr(Text, triggers.Text.builder(intents.TEXT)),

    Tr(dest=Locale, factory=triggers.Text.builder(intents.LOCALE)),

    Tr(Keyboard, triggers.Text.builder(intents.KEYBOARD)),
    Tr(origin=Keyboard, dest=Keyboard,
       factory=triggers.Action.builder('notif')),
    Tr(origin=Keyboard, dest=Keyboard,
       factory=triggers.Action.builder('alert')),
]
