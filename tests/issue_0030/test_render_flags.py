from bernard.conf.utils import (
    patch_conf,
)
from bernard.i18n.translator import (
    WordDictionary,
)


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
    with patch_conf({'I18N_TRANSLATION_LOADERS': []}):
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


def test_multi_sentence_reverse():
    with patch_conf({'I18N_TRANSLATION_LOADERS': []}):
        wd = WordDictionary()

        wd.update_lang(None, [
            ('HELLO+1', 'hello'),
            ('HELLO+2', 'wassup?'),
        ], {'gender': 'unknown'})

        wd.update_lang(None, [
            ('HELLO+2', 'wassup girl?'),
        ], {'gender': 'female'})

        wd.update_lang(None, [
            ('HELLO+2', 'wassup boy?'),
        ], {'gender': 'male'})

        assert wd.get('HELLO', flags={
            'gender': 'male'
        }) == ['hello', 'wassup boy?']

        assert wd.get('HELLO', flags={
            'gender': 'female'
        }) == ['hello', 'wassup girl?']


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
