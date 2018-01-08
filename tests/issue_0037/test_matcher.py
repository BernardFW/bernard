from bernard.trigram import Trigram, LabelMatcher


def test_label_matcher():
    lst = [
        (Trigram('foo'), 1),
        (Trigram('bar'), 2),
        (Trigram('baz'), 3),
    ]

    m = LabelMatcher(lst)

    assert m.similarity(Trigram('bar')) == (1.0, 2)
