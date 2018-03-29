import os

from bernard.conf.utils import (
    patch_conf,
)
from bernard.i18n.intents import (
    IntentsDb,
    IntentsMaker,
)
from bernard.utils import (
    run,
)

INTENTS_FILE_FR_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans_fr.csv',
)

INTENTS_FILE_EN_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans_en.csv',
)

LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': INTENTS_FILE_FR_PATH,
            'locale': 'fr',
        }
    },
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': INTENTS_FILE_EN_PATH,
            'locale': 'en',
        }
    },
]

LOADER_CONFIG = {
    'I18N_INTENTS_LOADERS': LOADERS,
}


class MockUser(object):
    async def get_timezone(self):
        return None


class MockRequest(object):
    locale = None
    user = MockUser()

    async def get_locale(self):
        return self.locale


def test_get_strings():
    with patch_conf(LOADER_CONFIG):
        db = IntentsDb()
        maker = IntentsMaker(db)
        req = MockRequest()

        assert run(maker.HELLO.strings()) == [('Bonjour',)]

        req.locale = 'fr'
        assert run(maker.HELLO.strings(req)) == [('Bonjour',)]

        req.locale = 'en'
        assert run(maker.HELLO.strings(req)) == [('Hello',)]

        req.locale = 'de'
        assert run(maker.HELLO.strings(req)) == [('Bonjour',)]
