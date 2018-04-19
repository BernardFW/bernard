# coding: utf-8
import hmac
from hashlib import (
    sha1,
)
from typing import (
    ByteString,
    Text,
)

from aiohttp.web_request import (
    Request,
)
from aiohttp.web_response import (
    Response,
    json_response,
)

import ujson
from bernard.platforms import (
    manager,
)
from bernard.platforms.facebook.platform import (
    Facebook,
    FacebookMessage,
)


def sign_message(body: ByteString, secret: Text) -> Text:
    """
    Compute a message's signature.
    """

    return 'sha1={}'.format(
        hmac.new(secret.encode(), body, sha1).hexdigest()
    )


def find_secret(page_id: Text):
    """
    Find the matching secret of a page ID.
    """

    for page in Facebook.settings():
        if page['page_id'] == page_id:
            return page['app_secret']


async def check_hook(request: Request):
    """
    That hook gets called when Facebook wants to check that the bot is
    responsive.
    """

    verify_token = request.query.get('hub.verify_token')

    if not verify_token:
        return json_response({
            'error': 'No verification token was provided',
        }, status=400)

    for page in Facebook.settings():
        if verify_token == page['security_token']:
            return Response(text=request.query.get('hub.challenge', ''))

    return json_response({
        'error': 'could not find the page token in configuration.'
    })


async def receive_events(request: Request):
    """
    Here Facebook might send us a bunch of events/messages that we need to
    handle.

    The JSON's body is checked using the signature provided in the headers then
    different message objects are created and forwarded to the FSM.
    """

    body = await request.read()
    try:
        content = ujson.loads(body)
    except ValueError:
        return json_response({
            'error': True,
            'message': 'Cannot decode body'
        }, status=400)
    page_id = content['entry'][0]['id']
    secret = find_secret(page_id)
    actual_sig = request.headers['X-Hub-Signature']
    expected_sig = sign_message(body, secret)

    if not hmac.compare_digest(actual_sig, expected_sig):
        return json_response({
            'error': True,
            'message': 'Invalid signature'
        }, status=401)

    fb = await manager.get_platform('facebook')

    for entry in content['entry']:
        for raw_message in entry.get('messaging', []):
            message = FacebookMessage(raw_message, fb)
            await fb.handle_event(message)

    return json_response({
        'ok': True,
    })
