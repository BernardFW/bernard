# coding: utf-8
import os
import sys

# Are we in debug mode?
# So far it changes nothing, but hey who knows.
DEBUG = os.getenv('DEBUG') == 'yes'

# Enable live reloading of the code
CODE_LIVE_RELOAD = (DEBUG and sys.platform in {'linux', 'linux2'}) or \
                   os.getenv('CODE_LIVE_RELOAD') == 'yes'

# How long to wait before starting the reload
CODE_RELOAD_DEBOUNCE = 1.0

# Live reload exit code
CODE_RELOAD_EXIT = 42

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

# Default lang
I18N_DEFAULT_LANG = 'en'

# Enable automatic reload of translation/intents files
I18N_LIVE_RELOAD = (DEBUG and sys.platform in {'linux', 'linux2'}) or \
                   os.getenv('I18N_LIVE_RELOAD') == 'yes'

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

# Secret used to validate user ID/page ID in a webview. It is supposed to be
# a string but is set to none in order for things to fail if this key is not
# set properly.
WEBVIEW_SECRET_KEY = None

# JWT algorithm
WEBVIEW_JWT_ALGORITHM = 'HS256'

# Where to store the webview token
WEBVIEW_TOKEN_KEY = '_bnd_user'

# Webviews are supposed to send a message when they close. However, it can
# happen on some shitty devices (follow my eyes) that connections are not
# closed properly. In this case, if we receive no heartbeat for X seconds then
# the webview is considered closed.
WEBVIEW_HEARTBEAT_TIMEOUT = 5.0

# Related to previous setting, the webview sends a heartbeat periodically to
# let us know that it is still open
WEBVIEW_HEARTBEAT_PERIOD = 1.0

# Sentry configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
