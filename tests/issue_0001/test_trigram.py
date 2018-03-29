# coding: utf-8
import pytest

from bernard.trigram import (
    Matcher,
    Trigram,
    make_trigrams,
    make_words,
    normalize,
)


def test_normalize():
    assert normalize('TOTO') == 'toto'
    assert normalize('éléphant') == 'elephant'
    assert normalize('     salut    bonjour    ') == 'salut bonjour'
    assert normalize('  SALUT,  ÉLÉPHANT   ') == 'salut elephant'
    assert normalize('aimes-tu les saucisses ?') == 'aimes tu les saucisses'


def test_make_words():
    assert make_words('aimes tu les saucisses') == \
           ['aimes', 'tu', 'les', 'saucisses']


def test_make_trigrams():
    assert list(make_trigrams('bonjour')) == [
        (' ', ' ', 'b'),
        (' ', 'b', 'o'),
        ('b', 'o', 'n'),
        ('o', 'n', 'j'),
        ('n', 'j', 'o'),
        ('j', 'o', 'u'),
        ('o', 'u', 'r'),
        ('u', 'r', ' '),
    ]

    assert list(make_trigrams('')) == []

    assert list(make_trigrams('a')) == [
        (' ', ' ', 'a'),
        (' ', 'a', ' '),
    ]

    assert list(make_trigrams('ab')) == [
        (' ', ' ', 'a'),
        (' ', 'a', 'b'),
        ('a', 'b', ' '),
    ]



def test_make_trigrams_like_psql():
    text = 'aimes-tu les saucisses ?  aimes-tu les bananes ?'
    trgms = set(tuple(x) for x in [
        '  a',
        '  b',
        '  l',
        '  s',
        '  t',
        ' ai',
        ' ba',
        ' le',
        ' sa',
        ' tu',
        'aim',
        'ana',
        'ane',
        'auc',
        'ban',
        'cis',
        'es ',
        'ime',
        'iss',
        'les',
        'mes',
        'nan',
        'nes',
        'sau',
        'ses',
        'sse',
        'tu ',
        'uci',
    ])

    t = Trigram(text)
    assert t._trigrams == trgms


def test_similarity():
    assert Trigram('bonjour') % Trigram('bnjour') == 0.5

    sim = Trigram('Aimes-tu les saucisses ?') % \
          Trigram('Aimes-tu les bananes ?')
    assert sim == pytest.approx(0.428571, 0.00001)


def test_matcher():
    m = Matcher([
        Trigram('hello'),
        Trigram('hi'),
        Trigram('saluton'),
        Trigram('ciao'),
        Trigram('bonjour'),
        Trigram('hé'),
    ])

    assert m % Trigram('he') == 1.0
