from bernard.i18n.translator import WordDictionary, Translator, render
from bernard.utils import run


def test_render_param():
    wd = WordDictionary()
    wd.update_lang('fr', [
        ('FOO', 'foo'),
        ('BAR', '{foo}'),
    ])

    t = Translator(wd)

    # noinspection PyTypeChecker
    assert run(render(t('BAR', foo=t.FOO), None)) == 'foo'
