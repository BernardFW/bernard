import os

from bernard.conf.utils import patch_conf
from bernard.i18n import Translator
from bernard.i18n.translator import WordDictionary
from bernard.utils import run

TRANS_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    "assets",
    "trans.csv",
)

LOADERS = [
    {
        "loader": "bernard.i18n.loaders.CsvTranslationLoader",
        "params": {
            "file_path": TRANS_FILE_PATH,
            "flags": {
                1: {"gender": "unknown"},
                2: {"gender": "male"},
                3: {"gender": "female"},
            },
        },
    },
]

LOADER_CONFIG = {
    "I18N_TRANSLATION_LOADERS": LOADERS,
}


class MockUser(object):
    async def get_timezone(self):
        return None


class MockRequest(object):
    locale = None
    flags = {}
    user = MockUser()

    async def get_locale(self):
        return self.locale

    async def get_trans_flags(self):
        return self.flags


def test_render():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        t = Translator(wd)
        req = MockRequest()

        req.flags = {"gender": "unknown"}
        assert run(t.HELLO.render_list(req)) == ["hello", "wassup?"]

        req.flags = {"gender": "male"}
        assert run(t.HELLO.render_list(req)) == ["hello boy", "wassup?"]

        req.flags = {"gender": "female"}
        assert run(t.HELLO.render_list(req)) == ["hello girl", "wassup?"]
