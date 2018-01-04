from bernard.i18n.translator import TransItem, Sentence, SentenceGroup, \
    SortingDict


def test_sentence():
    item1 = TransItem('FOO', 1, 'foo 1', {})
    item2 = TransItem('FOO', 1, 'foo 2', {})

    s = Sentence()
    assert not s.check()

    s.append(item1)
    s.append(item2)
    assert s.check()

    assert isinstance(s.render({}), str)
    assert s.render({}) in ['foo 1', 'foo 2']


def test_sentence_group():
    item1 = TransItem('FOO', 1, 'foo 1', {})
    item2 = TransItem('FOO', 2, 'foo 2', {})

    sg = SentenceGroup()
    assert not sg.check()

    sg.append(item2)
    assert not sg.check()

    sg.append(item1)
    assert sg.check()

    assert sg.render({}) == ['foo 1', 'foo 2']


def test_sorting_group():
    item1 = TransItem('FOO', 1, 'foo 1', {})
    item2 = TransItem('FOO', 2, 'foo 2', {})
    item3 = TransItem('BAR', 1, 'bar', {})

    sd = SortingDict()
    assert sd.extract() == {}

    sd.append(item1)
    assert set(sd.extract().keys()) == {'FOO'}

    sd.append(item3)
    assert set(sd.extract().keys()) == {'FOO', 'BAR'}

    data = sd.extract()
    assert data['BAR'].render({}) == ['bar']
