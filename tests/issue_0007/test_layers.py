import os

from bernard.conf.utils import patch_conf
from bernard.i18n import Translator
from bernard.platforms.telegram.layers import KeyboardButton, \
    ContactKeyboardButton, LocationKeyboardButton, ReplyKeyboard, \
    ReplyKeyboardRemove, AnswerCallbackQuery, InlineKeyboard, \
    InlineKeyboardButton
from bernard.utils import run

TRANS_FILE_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'trans.csv',
)

LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': TRANS_FILE_PATH,
            'locale': 'fr',
        }
    },
]

LOADER_CONFIG = {
    'I18N_TRANSLATION_LOADERS': LOADERS,
}


def test_keyboard_button():
    with patch_conf(LOADER_CONFIG):
        t = Translator()
        kb = KeyboardButton(t.HELLO)
        ser = run(kb.serialize(None))
        assert ser == {
            'text': 'Hello'
        }


def test_keyboard_contact_button():
    kb = ContactKeyboardButton('foo')
    assert run(kb.serialize(None)) == {
        'text': 'foo',
        'request_contact': True
    }


def test_keyboard_location_button():
    kb = LocationKeyboardButton('foo')
    assert run(kb.serialize(None)) == {
        'text': 'foo',
        'request_location': True
    }


def test_keyboard_button_eq():
    k1 = LocationKeyboardButton('foo')
    k2 = ContactKeyboardButton('foo')

    assert k1 != k2
    assert k1 == k1


def test_keyboard_serialize():
    k = ReplyKeyboard(
        [[LocationKeyboardButton('foo')]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True,
    )

    assert run(k.serialize(None)) == {
        'keyboard': [[{
            'text': 'foo',
            'request_location': True,
        }]],
        'resize_keyboard': True,
        'one_time_keyboard': True,
        'selective': True,
    }


def test_reply_keyboard_remove():
    k = ReplyKeyboardRemove(False)
    assert k.serialize() == {
        'remove_keyboard': True,
        'selective': False,
    }


def test_acq_serialize():
    with patch_conf(LOADER_CONFIG):
        t = Translator()
        acq = AnswerCallbackQuery(
            text=t.HELLO,
            show_alert=False,
            url='http://google.fr',
            cache_time=42,
        )

        assert run(acq.serialize('foo', None)) == {
            'callback_query_id': 'foo',
            'text': 'Hello',
            'show_alert': False,
            'url': 'http://google.fr',
            'cache_time': 42,
        }


def test_inline_keyboard():
    with patch_conf(LOADER_CONFIG):
        t = Translator()
        k = InlineKeyboard([[
            InlineKeyboardButton(text=t.HELLO),
        ]])

        assert run(k.serialize(None)) == {
            'inline_keyboard': [[{
                'text': 'Hello',
            }]],
        }


def test_patch_register():
    register = {}

    k = ReplyKeyboard([[KeyboardButton(
        text='Foo',
        choice='foo',
    )]])

    run(k.patch_register(register, None))

    assert register == {
        'choices': {
            'foo': {
                'intent': None,
                'text': 'Foo',
            }
        }
    }
