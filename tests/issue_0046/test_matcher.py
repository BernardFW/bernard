from bernard.trigram import Matcher, Trigram


def test_thanks():
    m = Matcher([
        (Trigram('thanks'), Trigram('no thanks'), Trigram('thank you not')),
    ])

    assert m.similarity(Trigram('thanks')) == 1.0
    assert m.similarity(Trigram('no thanks')) == 0.0
    assert m.similarity(Trigram('thank you not')) == 0.0
