# coding: utf-8
import asyncio
import os
import pytest
from bernard.i18n.loaders import BaseLoader, CsvLoader
from unittest.mock import Mock


# noinspection PyProtectedMember
def test_events_spreading():
    mock_cb = Mock()
    data = {'updated': 'yes'}

    loader = BaseLoader()
    loader.on_update(mock_cb)
    loader._update(data)

    mock_cb.assert_called_once_with(data)


def test_load_csv():
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

    loader = CsvLoader()
    loader.on_update(mock_cb)
    asyncio.get_event_loop().run_until_complete(loader.load(file_path))

    mock_cb.assert_called_once_with(data)


def test_base_loader_is_abstract():
    loader = BaseLoader()
    with pytest.raises(NotImplementedError):
        asyncio.get_event_loop().run_until_complete(loader.load())
