import os
from bernard.conf.utils import patch_conf
from bernard.i18n.translator import WordDictionary, Translator
from bernard.utils import run

TRANS_FILE_FR_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans_fr.csv',
)

TRANS_FILE_EN_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans_en.csv',
)

LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': TRANS_FILE_FR_PATH,
            'locale': 'fr',
        }
    },
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': TRANS_FILE_EN_PATH,
            'locale': 'en',
        }
    },
]

LOADER_CONFIG_1 = {
    'I18N_TRANSLATION_LOADERS': LOADERS,
}

LOADER_CONFIG_2 = {
    'I18N_TRANSLATION_LOADERS': list(reversed(LOADERS)),
}


class MockUser(object):
    async def get_timezone(self):
        return None


class MockRequest(object):
    locale = None
    user = MockUser()

    async def get_locale(self):
        return self.locale


def test_locales_order():
    with patch_conf(LOADER_CONFIG_1):
        wd = WordDictionary()
        assert wd.list_locales() == ['fr', 'en']

    with patch_conf(LOADER_CONFIG_2):
        wd = WordDictionary()
        assert wd.list_locales() == ['en', 'fr']


# noinspection PyTypeChecker
def test_translate():
    with patch_conf(LOADER_CONFIG_1):
        wd = WordDictionary()
        t = Translator(wd)
        req = MockRequest()

        req.locale = 'fr'
        assert run(t.HELLO.render(req)) == 'Bonjour'

        req.locale = 'en'
        assert run(t.HELLO.render(req)) == 'Hello'

        req.locale = 'de'
        assert run(t.HELLO.render(req)) == 'Bonjour'
