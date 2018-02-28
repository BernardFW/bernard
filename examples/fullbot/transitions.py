# coding: utf-8

from bernard.engine import Tr, triggers
from bernard import layers as lyr
from bernard.i18n import intents
from .states import Text, Keyboard, Locale, TelegramPhoto

transitions = [
    Tr(Text, triggers.Text.builder(intents.TEXT)),

    Tr(dest=Locale, factory=triggers.Text.builder(intents.LOCALE)),

    Tr(Keyboard, triggers.Text.builder(intents.KEYBOARD)),
    Tr(dest=Keyboard, do_not_register=True,
       factory=triggers.Action.builder('notif')),
    Tr(dest=Keyboard, do_not_register=True,
       factory=triggers.Action.builder('alert')),
    Tr(dest=TelegramPhoto, do_not_register=True,
       factory=triggers.Layer.builder(lyr.Image)),
]
