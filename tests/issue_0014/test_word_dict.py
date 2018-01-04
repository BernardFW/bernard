from bernard.i18n.translator import WordDictionary, SentenceGroup


def test_parse_item():
    wd = WordDictionary()

    item = wd.parse_item('FOO', 'foo', {})
    assert item.index == 1
    assert item.key == 'FOO'
    assert item.value == 'foo'

    item = wd.parse_item('FOO+1', 'foo', {})
    assert item.index == 1
    assert item.key == 'FOO'
    assert item.value == 'foo'

    item = wd.parse_item('FOO+2', 'foo', {})
    assert item.index == 2
    assert item.key == 'FOO'
    assert item.value == 'foo'


def test_update_lang():
    wd = WordDictionary()
    wd.update_lang('fr', [
        ('FOO', 'foo'),
        ('BAR', 'bar'),
    ], {})

    assert 'fr' in wd.dict
    assert 'FOO' in wd.dict['fr']
    assert 'BAR' in wd.dict['fr']
    assert isinstance(wd.dict['fr']['FOO'], SentenceGroup)
    assert wd.dict['fr']['FOO'].render({}) == ['foo']


def test_update():
    wd = WordDictionary()
    wd.update({
        'fr': [
            ('FOO', 'foo'),
            ('BAR', 'bar'),
        ]
    })

    assert 'fr' in wd.dict
    assert 'FOO' in wd.dict['fr']
    assert 'BAR' in wd.dict['fr']
    assert isinstance(wd.dict['fr']['FOO'], SentenceGroup)
    assert wd.dict['fr']['FOO'].render({}) == ['foo']


def test_get():
    wd = WordDictionary()
    wd.update({
        None: [
            ('FOO+1', 'foo 1'),
            ('FOO+2', 'foo 2'),
        ]
    })

    assert wd.get('FOO') == ['foo 1', 'foo 2']
