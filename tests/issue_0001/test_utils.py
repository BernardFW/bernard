# coding: utf-8
from bernard.utils import (
    patch_qs,
)


def test_patch_qs():
    url = 'https://yolo.com/foo/bar?foo=1&bar=2'
    assert patch_qs(url, {'foo': '3'}) == \
        'https://yolo.com/foo/bar?bar=2&foo=3'

    url = 'http://test.com:42/foo'
    assert patch_qs(url, {}) == 'http://test.com:42/foo'
