# coding: utf-8
import os

# Are we in debug mode?
# So far it changes nothing, but hey who knows.
DEBUG = os.getenv('DEBUG') == 'yes'

# Bind to this host/port by default
SERVER_BIND = {
    'host': '::1',
    'port': '8666',
}

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

# Base score of a jumping trigger: if a transition can be triggered from the
# initial state but that there is a current state, then the trigger needs to
# make a jump in the graph. This is unnatural, so it gets a penalty. Still,
# we want it to be possible for users not to stay trapped in the same story
# forever if they don't want to finish it.
JUMPING_TRIGGER_PENALTY = 0.8

# Below this score, the trigger isn't considered valid
MINIMAL_TRIGGER_SCORE = 0.3

# This is the state that handles error messages in case no other state is
# active (and something fails)
DEFAULT_STATE = 'bernard.engine.state.DefaultState'

# Configure here the Facebook pages you want to handle.
# Each item is expected to be like:
# {
#     'security_token': 'xxxx',
#     'app_secret': 'xxxx',
#     'page_id': 'xxxx',
#     'page_token': 'xxxx',
# }
FACEBOOK = []

# By default, store the register in local redis
REGISTER_STORE = {
    'class': 'bernard.storage.register.RedisRegisterStore',
    'params': {},
}

# Max internal jumps allowed. This is to avoid infinite loops in poorly
# configured transitions.
MAX_INTERNAL_JUMPS = 10
