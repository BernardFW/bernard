# coding: utf-8
import pytest
from collections import defaultdict
from bernard.storage.register import make_ro, RoDict, RoList, Register, \
    BaseRegisterStore
from bernard.utils import run

SAMPLE_DATA = {
    'foo': 'bar',
    'one': {
        'two': 'three',
    },
    'four': ['five', 'six', {'seven': 'eight'}],
    'nine': 10,
    'eleven': 12.0,
    'thirteen': None,
    'fourteen': True,
}


def test_make_ro():
    d = make_ro(SAMPLE_DATA)
    assert isinstance(d, RoDict)
    assert d['foo'] == 'bar'
    assert len(d) == 7
    assert [x for x in d] == [x for x in SAMPLE_DATA]
    assert isinstance(d['four'], RoList)
    assert isinstance(d['nine'], int)
    assert isinstance(d['eleven'], float)
    assert d['thirteen'] is None
    assert isinstance(d['fourteen'], bool)
    assert len(d['four']) == 3
    assert isinstance(d['four'][2], RoDict)


def test_ro_on_ro():
    d = make_ro(SAMPLE_DATA)
    d = make_ro(d)
    assert d['foo'] == 'bar'


def test_ro_fail():
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        make_ro(object())


def test_register_init():
    r = Register({})
    assert r.replacement is None


class MockRegisterStore(BaseRegisterStore):
    def __init__(self):
        self.called = defaultdict(lambda: False)

    async def _start(self, key):
        assert key == 'my-key'
        self.called['start'] = True

    async def _get(self, key):
        assert key == 'my-key'
        self.called['get'] = True
        return {'fake_context': True}

    async def _replace(self, key, data):
        assert key == 'my-key'
        assert data == {'new_data': True}
        self.called['replace'] = True

    async def _finish(self, key):
        assert key == 'my-key'
        self.called['finish'] = True


def test_register_context_manager():
    store = MockRegisterStore()

    async def test():
        async with store.work_on_register('my-key') as reg:
            assert store.called['start']
            assert store.called['get']
            assert isinstance(reg, Register)
            assert reg == {'fake_context': True}
            reg.replacement = {'new_data': True}

        assert store.called['replace']
        assert store.called['finish']

    run(test())
