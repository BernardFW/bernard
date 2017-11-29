from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from bernard.engine.request import Request
    from bernard.layers.stack import Stack


async def set_reply_markup(msg: Dict, request: 'Request', stack: 'Stack') \
        -> None:
    """
    Add the "reply markup" to a message from the layers

    :param msg: Message dictionary
    :param request: Current request being replied
    :param stack: Stack to analyze
    """

    from bernard.platforms.telegram.layers import InlineKeyboard, \
        ReplyKeyboard, \
        ReplyKeyboardRemove

    try:
        keyboard = stack.get_layer(InlineKeyboard)
    except KeyError:
        pass
    else:
        msg['reply_markup'] = await keyboard.serialize(request)
    try:
        keyboard = stack.get_layer(ReplyKeyboard)
    except KeyError:
        pass
    else:
        msg['reply_markup'] = await keyboard.serialize(request)
    try:
        remove = stack.get_layer(ReplyKeyboardRemove)
    except KeyError:
        pass
    else:
        msg['reply_markup'] = remove.serialize()
