# coding: utf-8
from os import (
    getenv,
    path,
)
from urllib.parse import (
    urlparse,
)


def extract_domain(var_name, output):
    """
    Extracts just the domain name from an URL and adds it to a list
    """

    var = getenv(var_name)

    if var:
        p = urlparse(var)
        output.append(p.hostname)


def make_whitelist():
    """
    Generates the list of whitelisted domains for webviews. This is especially
    useful when you create your Facebook Messenger configuration.

    Don't hesitate to change this function to add more domains if you need it.
    """

    out = []
    extract_domain('BERNARD_BASE_URL', out)
    return out


def i18n_root(lang):
    """
    Computes the root to a given lang's root directory
    """

    return path.join(path.dirname(__file__), '../../i18n', lang)


# --- Starting points ---

# This module contains the transitions and is loaded to generate the FSM.
TRANSITIONS_MODULE = '__project_name_snake__.transitions'

# The default state is used whenever something goes wrong which prevents a
# state to be chosen. In this case, it will ball back to the default state
# in order to produce an error message. This default state must also be the
# common ancestor of all your states in order for them to inherit the default
# error messages.
DEFAULT_STATE = '__project_name_snake__.states.__project_name_camel__State'


# --- Platforms ---

# That's the configuration tokens for all the platforms you want to manage.
PLATFORMS = []

# Adds the Facebook support if Facebook tokens are detected. Don't forget
# to set everything right in the Facebook developers website
# https://developers.facebook.com/
if getenv('FB_PAGE_TOKEN'):
    PLATFORMS.append({
        'class': 'bernard.platforms.facebook.platform.Facebook',
        'settings': {
            'app_id': getenv('FB_APP_ID'),
            'app_secret': getenv('FB_APP_SECRET'),
            'page_id': getenv('FB_PAGE_ID'),
            'page_token': getenv('FB_PAGE_TOKEN'),
        },

        # https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api/greeting
        'greeting': [{
            'locale': 'default',
            'text': 'Welcome to this BERNARD bot!',
        }],

        # https://developers.facebook.com/docs/messenger-platform/send-messages/persistent-menu
        'menu': [{
            'locale': 'default',
            'call_to_actions': [
                {
                    'title': 'Get started again',
                    'type': 'postback',
                    'payload': '{"action": "get_started"}',
                },
            ]
        }],

        # https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api/domain-whitelisting
        'whitelist': make_whitelist(),
    })

# Adds Telegram support if Telegram tokens are detected. Don't forget to
# register and configure your bot by talking to @BotFather
if getenv('TELEGRAM_TOKEN'):
    PLATFORMS.append({
        'class': 'bernard.platforms.telegram.platform.Telegram',
        'settings': {
            'token': getenv('TELEGRAM_TOKEN'),
        },
    })


# --- Self-awareness ---

# Public base URL, used to generate links to the bot itself.
BERNARD_BASE_URL = getenv('BERNARD_BASE_URL')

# Secret key that serves in particular to sign content sent to the webview, but
# also in other places where signed content is required (aka when something
# goes outside and back again).
WEBVIEW_SECRET_KEY = getenv('WEBVIEW_SECRET_KEY')


# --- Network configuration ---

socket_path = getenv('SOCKET_PATH')

# That's a way to configure the network binding. If you define the SOCKET_PATH
# environment variable, then it will bind to the specified path as a UNIX
# socket. Otherwise it will look at BIND_PORT to know which TCP port to bind to
# and will fall back to 8666.
if socket_path:
    SERVER_BIND = {
        'path': socket_path,
    }
else:
    SERVER_BIND = {
        'host': '127.0.0.1',
        'port': int(getenv('BIND_PORT', '8666')),
    }


# --- Natural language understanding/generation ---

# List of intents loaders, typically CSV files with intents.
I18N_INTENTS_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'intents.csv'),
            'locale': 'en',
        },
    },
]

# List of translation loaders, typically CSV files with translations.
I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'responses.csv'),
            'locale': 'fr',
        },
    },
]


# --- Middlewares ---

# All your middlewares. The default ones are here to slow down the sending of
# messages and make it look more natural.
MIDDLEWARES = [
    'bernard.middleware.AutoSleep',
    'bernard.middleware.AutoType',
]

# Sleeping offset before any message
USERS_READING_BUBBLE_START = 0.0

# How many words per minute can your users read? This will compute the delay
# for each message automatically.
USERS_READING_SPEED = 400
