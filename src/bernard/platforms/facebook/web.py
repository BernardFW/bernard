# coding: utf-8
import hmac
import jwt
import re
import asyncio
import ujson
from textwrap import dedent
from urllib.parse import urljoin
from hashlib import sha1
from typing import Text, ByteString
from aiohttp.http_websocket import WSMsgType
from aiohttp.web_request import Request
from aiohttp.web_response import json_response, Response
from aiohttp.web_ws import WebSocketResponse
from bernard.platforms.facebook.platform import FacebookMessage
from bernard.platforms import manager
from bernard.conf import settings


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

    for page in settings.FACEBOOK:
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

    for page in settings.FACEBOOK:
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
            raw_message['url_base'] = str(request.url)
            message = FacebookMessage(raw_message, fb)
            await fb.handle_event(message)

    return json_response({
        'ok': True,
    })


async def redirect(request: Request):
    """
    This view redirects the user to another page using a JWT encoded URL. It
    will trigger a message for the user that clicked the link.
    """

    l = request.query.get('l')

    if not l:
        return json_response({
            'error': True,
            'message': 'Missing l argument'
        }, status=400)

    try:
        l = jwt.decode(l, settings.WEBVIEW_SECRET_KEY)
    except jwt.InvalidTokenError:
        return json_response({
            'error': True,
            'message': 'Provided token is invalid'
        }, status=400)

    try:
        user_id = l['u']
        assert isinstance(user_id, Text)
        page_id = l['p']
        assert isinstance(page_id, Text)
        url = l['h']
        assert isinstance(url, Text)
        slug = l['s']
        assert isinstance(slug, Text) or slug is None
    except (KeyError, AssertionError):
        return json_response({
            'error': True,
            'message': 'Provided payload is invalid'
        }, status=400)

    event = {
        'sender': {
            'id': user_id,
        },
        'recipient': {
            'id': page_id,
        },
        'url_base': str(request.url),
        'link_click': {
            'url': url,
            'slug': slug,
        },
    }

    ua = request.headers.get('user-agent', '')  # type: Text
    if not ua.startswith('facebookexternalhit'):
        fb = await manager.get_platform('facebook')
        msg = FacebookMessage(event, fb, False)
        await fb.handle_event(msg)

    return Response(
        headers={
            'Location': url,
        },
        status=302,
    )


async def unload_js(request: Request):
    """
    This generates a javascript that you can embed into any webview in order
    to enable webview closing events.

    You need to sign the webview using the `sign_webview` parameter of an
    UrlButton.

    If you want to close/change your page without triggering the page close
    event, you can call in JS `bernard.unloadNotifier.inhibit()`.
    """

    request_url = str(request.url)
    request_url = re.sub(r'^https?://', 'wss://', request_url)

    script = """
        (function () {
            var STORAGE_KEY = '_bnd_user';
            
            function UnloadNotifier() {
                var self = this,
                    intervalId,
                    ws;
                    
                function getSearch() {
                    if (window.location.search.indexOf('_bnd_user=') >= 0) {
                        sessionStorage.setItem(
                            STORAGE_KEY, 
                            window.location.search
                        );
                        
                        return window.location.search;
                    }
                    
                    var q = sessionStorage.getItem(STORAGE_KEY);
                    
                    if (q) {
                        return q;
                    }
                }

                function connect() {
                    search = getSearch();
                    
                    if (search) {
                        ws = new WebSocket(WS_URL + search);
                        ws.onopen = onConnect;
                    }
                }

                function onConnect() {
                    setInterval(beat, HEARTBEAT_PERIOD * 1000);
                }

                function beat() {
                    ws.send('beat');
                }

                function unload() {
                    ws.send('unload');
                    inhibit();
                }

                function inhibit() {
                    ws.send('inhibit');
                    clearInterval(intervalId);
                    ws.close();
                }

                self.inhibit = inhibit;
                self.unload = unload;

                (function () {
                    connect();
                    window.addEventListener('beforeunload', unload);
                }());
            }

            window.bernard = {
                unloadNotifier: new UnloadNotifier()
            };
        }());
    """

    script = script.replace(
        'WS_URL',
        ujson.dumps(urljoin(request_url, '/unload/facebook.sock'))
    )
    script = script.replace(
        'HEARTBEAT_PERIOD',
        ujson.dumps(settings.WEBVIEW_HEARTBEAT_PERIOD)
    )
    script = dedent(script).strip()

    return Response(text=script, content_type='text/javascript')


async def unload_sock(request: Request):
    """
    WebSocket view to detect when Messenger closes the WebView.

    There is a dual mechanism:

        - If "unload" is received over the socket, then close instantly
        - If no heartbeat is received for some time, them close

    The URL must include signed information about the user, like what
    the `sign_webview` parameter of UrlButton would provide.
    """

    tk = request.query.get(settings.WEBVIEW_TOKEN_KEY)

    if not tk:
        return json_response({
            'error': True,
            'message': 'Missing "{}"'.format(settings.WEBVIEW_TOKEN_KEY),
        }, status=400)

    try:
        tk = jwt.decode(tk, settings.WEBVIEW_SECRET_KEY)
    except jwt.InvalidTokenError:
        return json_response({
            'error': True,
            'message': 'Provided token is invalid'
        }, status=400)

    try:
        user_id = tk['fb_psid']
        assert isinstance(user_id, Text)
        page_id = tk['fb_pid']
        assert isinstance(page_id, Text)
        slug = tk['slug']
        assert isinstance(slug, Text) or slug is None
    except (KeyError, AssertionError):
        return json_response({
            'error': True,
            'message': 'Provided payload is invalid'
        }, status=400)

    event = {
        'sender': {
            'id': user_id,
        },
        'recipient': {
            'id': page_id,
        },
        'url_base': str(request.url),
        'close_webview': {
            'slug': slug,
        },
    }

    ws = WebSocketResponse(timeout=settings.WEBVIEW_HEARTBEAT_TIMEOUT,
                           receive_timeout=settings.WEBVIEW_HEARTBEAT_TIMEOUT)
    await ws.prepare(request)

    inhibit = False

    try:
        # noinspection PyTypeChecker
        async for msg in ws:
            # For some reason, the timeout does not work without a print
            # Yeah, what the fuck right?
            # TODO make it work properly
            print('hack print')
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'unload':
                    break
                if msg.data == 'inhibit':
                    inhibit = True
            elif msg.type == WSMsgType.ERROR:
                break
    except asyncio.TimeoutError:
        pass

    if not inhibit:
        fb = await manager.get_platform('facebook')
        msg = FacebookMessage(event, fb, False)
        await fb.handle_event(msg)

    return ws
