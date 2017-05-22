# coding: utf-8
from .translator import Translator, TransText, serialize, unserialize, render
from .intents import IntentsMaker

translate = Translator()
intents = IntentsMaker()
