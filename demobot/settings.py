# coding: utf-8

from os import getenv, path


FACEBOOK = [
    {
        'security_token': getenv('FB_SECURITY_TOKEN'),
        'app_secret': getenv('FB_APP_SECRET'),
        'page_id': getenv('FB_PAGE_ID'),
        'page_token': getenv('FB_PAGE_TOKEN'),
    }
]


SERVER_BIND = {
    'host': '127.0.0.1',
    'port': 8666,
}

REGISTER_STORE = {
    'class': 'bernard.storage.register.RedisRegisterStore',
    'params': {},
}

TRANSITIONS_MODULE = 'demobot.transitions'

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
