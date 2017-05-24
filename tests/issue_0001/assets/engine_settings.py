import os

REGISTER_STORE = {
    'class': 'bernard.storage.register.RedisRegisterStore',
    'params': {},
}

TRANSITIONS_MODULE = 'tests.issue_0001.transitions'

I18N_INTENTS_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': os.path.join(
                os.path.dirname(__file__),
                'engine_intents.csv',
            )
        }
    }
]

I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': os.path.join(
                os.path.dirname(__file__),
                'engine_responses.csv',
            ),
        }
    }
]

DEFAULT_STATE = 'tests.issue_0001.states.BaseTestState'
