# coding: utf-8

from os import getenv, path


PLATFORMS = []

if getenv('FB_PAGE_TOKEN'):
    PLATFORMS.append({
        'class': 'bernard.platforms.facebook.platform.Facebook',
        'settings': [
            {
                'security_token': getenv('FB_SECURITY_TOKEN'),
                'app_secret': getenv('FB_APP_SECRET'),
                'page_id': getenv('FB_PAGE_ID'),
                'page_token': getenv('FB_PAGE_TOKEN'),
            },
        ],
    })

if getenv('TELEGRAM_TOKEN'):
    PLATFORMS.append({
        'class': 'bernard.platforms.telegram.platform.Telegram',
        'settings': {
            'token': getenv('TELEGRAM_TOKEN'),
        },
    })

BERNARD_BASE_URL = getenv('BERNARD_BASE_URL')

DEFAULT_STATE = 'fullbot.states.BaseTestState'

SERVER_BIND = {
    'host': '127.0.0.1',
    'port': 8666,
}

REGISTER_STORE = {
    'class': 'bernard.storage.register.RedisRegisterStore',
    'params': {},
}

TRANSITIONS_MODULE = 'fullbot.transitions'

I18N_INTENTS_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': path.join(
                path.dirname(__file__),
                'i18n',
                'fr',
                'intents.csv',
            )
        }
    }
]

I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(
                path.dirname(__file__),
                'i18n',
                'fr',
                'responses.csv',
            ),
        }
    }
]

WEBVIEW_SECRET_KEY = 'wegpijwgpweojg'
