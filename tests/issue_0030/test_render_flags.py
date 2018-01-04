from bernard.i18n.translator import WordDictionary


def test_render_gender():
    wd = WordDictionary()

    wd.update_lang(None, [
        ('PRONOUN', 'he'),
    ], {'gender': 'male'})

    wd.update_lang(None, [
        ('PRONOUN', 'she'),
    ], {'gender': 'female'})

    assert wd.get('PRONOUN', flags={'gender': 'male'}) == ['he']
    assert wd.get('PRONOUN', flags={'gender': 'female'}) == ['she']


def test_multi_sentence():
    wd = WordDictionary()

    wd.update_lang(None, [
        ('HELLO+1', 'hello'),
        ('HELLO+2', 'wassup?'),
    ], {'gender': 'unknown'})

    wd.update_lang(None, [
        ('HELLO+1', 'hello girl'),
    ], {'gender': 'female'})

    wd.update_lang(None, [
        ('HELLO+1', 'hello boy'),
    ], {'gender': 'male'})

    assert wd.get('HELLO', flags={
        'gender': 'male'
    }) == ['hello boy', 'wassup?']

    assert wd.get('HELLO', flags={
        'gender': 'female'
    }) == ['hello girl', 'wassup?']


def test_update_flags():
    wd = WordDictionary()

    wd.update_lang(None, [
        ('PRONOUN', 'he'),
    ], {'gender': 'male'})

    wd.update_lang(None, [
        ('PRONOUN', 'she'),
    ], {'gender': 'female'})

    wd.update_lang(None, [
        ('PRONOUN', 'her'),
    ], {'gender': 'female'})

    assert wd.get('PRONOUN', flags={'gender': 'male'}) == ['he']
    assert wd.get('PRONOUN', flags={'gender': 'female'}) == ['her']
