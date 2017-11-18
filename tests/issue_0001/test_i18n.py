# coding: utf-8
import os
import pytest
import pytz
import datetime
# noinspection PyProtectedMember
from bernard.i18n._formatter import make_date
from bernard.i18n.translator import *
from bernard.i18n.loaders import BaseTranslationLoader, CsvTranslationLoader, \
    BaseIntentsLoader, CsvIntentsLoader
from bernard.i18n.intents import Intent, IntentsMaker, IntentsDb
from bernard.conf.utils import patch_conf
from bernard.utils import run
from dateutil import tz
from unittest.mock import Mock


TRANS_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans.csv',
)

LOADER_CONFIG = {
    'I18N_TRANSLATION_LOADERS': [
        {
            'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
            'params': {
                'file_path': TRANS_FILE_PATH,
            }
        }
    ]
}

LOADER_CONFIG_2 = {
    'I18N_TRANSLATION_LOADERS': [
        {
            'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
            'params': {
                'file_path': os.path.join(
                    os.path.dirname(__file__),
                    'assets',
                    'trans2.csv',
                ),
            }
        }
    ]
}

LOADER_CONFIG_3 = {
    'I18N_INTENTS_LOADERS': [
        {
            'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
            'params': {
                'file_path': os.path.join(
                    os.path.dirname(__file__),
                    'assets',
                    'intents.csv',
                )
            }
        }
    ]
}


# noinspection PyProtectedMember
def test_translations_events_spreading():
    mock_cb = Mock()
    data = {None: {'updated': 'yes'}}

    loader = BaseTranslationLoader()
    loader.on_update(mock_cb)
    loader._update(data)

    mock_cb.assert_called_once_with(data)


# noinspection PyProtectedMember
def test_intents_events_spreading():
    mock_cb = Mock()
    data = {None: {'updated': ['yes']}}

    loader = BaseIntentsLoader()
    loader.on_update(mock_cb)
    loader._update(data)

    mock_cb.assert_called_once_with(data)


def test_load_translations_csv():
    mock_cb = Mock()
    data = {
        'FOO': 'éléphant',
        'BAR': 'baz',
    }

    loader = CsvTranslationLoader()
    loader.on_update(mock_cb)
    run(loader.load(file_path=TRANS_FILE_PATH))

    mock_cb.assert_called_once_with({None: data})


def test_base_translations_loader_is_abstract():
    loader = BaseTranslationLoader()
    with pytest.raises(NotImplementedError):
        run(loader.load())


def test_base_intents_loader_is_abstract():
    loader = BaseIntentsLoader()
    with pytest.raises(NotImplementedError):
        run(loader.load())


def test_load_intents_csv():
    mock_cb = Mock()
    data = {
        'FOO': ['bar', 'baz'],
        'BAR': ['ᕕ( ՞ ᗜ ՞ )ᕗ', '∩༼˵☯‿☯˵༽つ¤=[]:::::>', 'c( ⁰ 〰 ⁰ )੭'],
        'BAZ': ['foo'],
    }
    file_path = os.path.join(
        os.path.dirname(__file__),
        'assets',
        'intents.csv',
    )

    loader = CsvIntentsLoader()
    loader.on_update(mock_cb)
    run(loader.load(file_path=file_path))

    mock_cb.assert_called_once_with({None: data})


def test_word_dict():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        assert wd.get('FOO') == 'éléphant'


def test_word_dict_count():
    wd = WordDictionary()

    with pytest.raises(TranslationError):
        wd.get('FOO', 1)


def test_word_dict_missing():
    wd = WordDictionary()

    with pytest.raises(MissingTranslationError):
        wd.get('DOES_NOT_EXIST')


def test_word_dict_param():
    with patch_conf(LOADER_CONFIG_2):
        wd = WordDictionary()
        assert wd.get('WITH_PARAM', name='Mike') == 'Hello Mike'


def test_word_dict_missing_param():
    with patch_conf(LOADER_CONFIG_2):
        wd = WordDictionary()

        with pytest.raises(MissingParamError):
            wd.get('WITH_PARAM')


def test_translator_call():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        t = Translator(wd)
        s = t('FOO', 42, bar='baz')

        assert s.key == 'FOO'
        assert s.count == 42
        assert s.params == {'bar': 'baz'}


def test_translator_attr():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        t = Translator(wd)
        s = t.FOO

        assert s.key == 'FOO'
        assert s.count is None
        assert s.params == {}


def test_translate_render():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        t = Translator(wd)

        assert run(t.FOO.render()) == 'éléphant'


def test_translate_singleton():
    from bernard.i18n import translate as t
    assert isinstance(t, Translator)


def test_serialize():
    assert serialize('foo') == {
        'type': 'string',
        'value': 'foo',
    }

    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()
        t = Translator(wd)
        s = t.FOO

        assert serialize(s) == {
            'type': 'trans',
            'key': 'FOO',
            'count': None,
            'params': {},
        }


def test_unserialize():
    with patch_conf(LOADER_CONFIG):
        wd = WordDictionary()

        v = 42
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            unserialize(wd, v)

        v = {}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {'type': 'string'}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {'type': 'trans'}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {'type': 'trans', 'params': 42}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {'type': 'trans', 'params': {42: True}}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {'type': 'trans', 'params': {'42': True}}
        with pytest.raises(ValueError):
            unserialize(wd, v)

        v = {
            'type': 'trans',
            'params': {'42': True},
            'key': 'FOO',
            'count': None
        }
        assert isinstance(unserialize(wd, v), StringToTranslate)

        v = {'type': 'string', 'value': 'foo'}
        assert unserialize(wd, v) == 'foo'


def test_intents_db():
    with patch_conf(LOADER_CONFIG_3):
        db = IntentsDb()
        assert db.get('FOO', None) == ['bar', 'baz']


def test_intent():
    with patch_conf(LOADER_CONFIG_3):
        db = IntentsDb()
        intent = Intent(db, 'FOO')
        assert run(intent.strings()) == ['bar', 'baz']


def test_intents_maker():
    with patch_conf(LOADER_CONFIG_3):
        db = IntentsDb()
        maker = IntentsMaker(db)
        assert run(maker.FOO.strings()) == ['bar', 'baz']


def test_intents_maker_singleton():
    with patch_conf(LOADER_CONFIG_3):
        from sys import modules
        if 'bernard.i18n' in modules:
            del modules['bernard.i18n']

        from bernard.i18n import intents as i
        assert run(i.FOO.strings()) == ['bar', 'baz']


def test_make_date():
    d = datetime.date(2000, 1, 1)
    assert make_date(d) == d

    d2 = datetime.datetime(2000, 1, 1, 0, 0)
    assert make_date(d2) == d

    d3 = '2000-01-01T00:00:00.000000Z'
    assert make_date(d3) == d

    test_tz = pytz.timezone('America/Cancun')
    assert make_date(d3, test_tz) != d

    test_tz = tz.tzoffset('IST', -3600)
    assert make_date(d3, test_tz) != d


def test_format_date():
    test_tz = tz.tzoffset('IST', -3600)
    f = I18nFormatter('fr', test_tz)

    d = '2000-01-01T00:00:00.000000Z'

    assert f.format('Posté le {post_date:date:medium}', post_date=d) == \
        'Posté le 1 janv. 2000'
