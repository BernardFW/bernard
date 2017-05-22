# coding: utf-8
import os

# Are we in debug mode?
# So far it changes nothing, but hey who knows.
DEBUG = os.getenv('DEBUG') == 'yes'

# List of translation loaders. Empty by default so it doesn't crash, but you
# need to specify your own.
I18N_TRANSLATION_LOADERS = []

# List of intents loaders.
I18N_INTENTS_LOADERS = []

# How long should a register lock last? Registers are locked when starting to
# answer a message and freed when the response is sent. One minute sounds
# reasonable.
REGISTER_LOCK_TIME = 60

# How fast to poll redis for locks? There is no real good reason to change
# this, it is simply here to be able to speed up some tests
REDIS_POLL_INTERVAL = 1
