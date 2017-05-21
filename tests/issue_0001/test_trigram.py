# coding: utf-8
from bernard.trigram import normalize, make_trigrams, Trigram, Matcher


def test_normalize():
    assert normalize('TOTO') == 'toto'
    assert normalize('éléphant') == 'elephant'
    assert normalize('salut, bonjour') == 'salut,bonjour'
    assert normalize('     salut    bonjour    ') == 'salut bonjour'
    assert normalize('  SALUT,  ÉLÉPHANT   ') == 'salut,elephant'


def test_make_trigrams():
    assert list(make_trigrams('bonjour')) == [
        (None, None, 'b'),
        (None, 'b', 'o'),
        ('b', 'o', 'n'),
        ('o', 'n', 'j'),
        ('n', 'j', 'o'),
        ('j', 'o', 'u'),
        ('o', 'u', 'r'),
        ('u', 'r', None),
    ]

    assert list(make_trigrams('')) == []

    assert list(make_trigrams('a')) == [
        (None, None, 'a'),
        (None, 'a', None),
    ]

    assert list(make_trigrams('ab')) == [
        (None, None, 'a'),
        (None, 'a', 'b'),
        ('a', 'b', None),
    ]


def test_similarity():
    # TODO make this test more comprehensive (in particular, this is not
    # consistent with PostgreSQL)
    assert Trigram('bonjour') % Trigram('bnjour') == 0.5


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
