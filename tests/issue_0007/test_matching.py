from bernard import (
    layers as lyr,
)
from bernard.platforms.telegram import (
    layers as tgr,
)
from bernard.utils import (
    ClassExp,
)


def test_markdown():
    pattern = ('^Markdown+ '
               '(InlineKeyboard|ReplyKeyboard|ReplyKeyboardRemove)? '
               'Reply?$'

               '|^Markdown InlineKeyboard? Reply? Update$')

    ce = ClassExp(pattern)

    assert repr(ce._compiled_expression) == \
        "re.compile('^(?:Markdown,)+((?:InlineKeyboard,)|(?:ReplyKeyboard,)|" \
        "(?:ReplyKeyboardRemove,))?(?:Reply,)?$" \
        "|^(?:Markdown,)(?:InlineKeyboard,)?(?:Reply,)?(?:Update,)$')"

    assert ce.match([
        lyr.Markdown(''),
        tgr.InlineKeyboard([]),
        tgr.Reply(),
        tgr.Update(),
    ])
