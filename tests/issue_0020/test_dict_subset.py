from bernard.utils import (
    dict_is_subset,
)


def test_basic_positive():
    full_set = {
        'a': 1,
        'b': 2,
    }

    small_set = {
        'a': 1,
    }

    assert dict_is_subset(small_set, full_set)


def test_basic_negative():
    full_set = {
        'a': 1,
        'b': 2,
    }

    small_set = {
        'a': 2,
    }

    assert not dict_is_subset(small_set, full_set)


def test_on_list():
    full_set = [{
        'a': 1,
        'b': 2,
    }]

    small_set = [{
        'a': 1,
    }]

    assert dict_is_subset(small_set, full_set)


def test_recursive():
    full_set = {
        'c': [{
            'a': 1,
            'b': 2,
        }]
    }

    small_set = {
        'c': [{
            'a': 1,
        }],
    }

    assert dict_is_subset(small_set, full_set)


def test_recursive_negative():
    full_set = {
        'c': [{
            'a': 1,
            'b': 2,
        }]
    }

    small_set = {
        'c': [{
            'a': 3,
        }],
    }

    assert not dict_is_subset(small_set, full_set)


def test_key_not_there():
    full_set = {}
    small_set = {'a': 1}

    assert not dict_is_subset(small_set, full_set)
