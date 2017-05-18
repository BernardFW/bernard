# coding: utf-8
import asyncio
import os
import pytest
from bernard.i18n.loaders import BaseTranslationLoader, CsvTranslationLoader, \
    BaseIntentsLoader, CsvIntentsLoader
from unittest.mock import Mock


def run(task):
    asyncio.get_event_loop().run_until_complete(task)


# noinspection PyProtectedMember
def test_translations_events_spreading():
    mock_cb = Mock()
    data = {'updated': 'yes'}

    loader = BaseTranslationLoader()
    loader.on_update(mock_cb)
    loader._update(data)

    mock_cb.assert_called_once_with(data)


# noinspection PyProtectedMember
def test_intents_events_spreading():
    mock_cb = Mock()
    data = {'updated': ['yes']}

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
    file_path = os.path.join(
        os.path.dirname(__file__),
        'assets',
        'trans.csv',
    )

    loader = CsvTranslationLoader()
    loader.on_update(mock_cb)
    run(loader.load(file_path=file_path))

    mock_cb.assert_called_once_with(data)


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
    }
    file_path = os.path.join(
        os.path.dirname(__file__),
        'assets',
        'intents.csv',
    )

    loader = CsvIntentsLoader()
    loader.on_update(mock_cb)
    run(loader.load(file_path=file_path))

    mock_cb.assert_called_once_with(data)
