from bernard.layers import FbButtonTemplate, FbUrlButton, FbShareButton, \
    FbGenericTemplate, FbCard, stack
from bernard.platforms.facebook.platform import Facebook
from bernard.utils import run
from unittest.mock import patch


async def instant_run():
    pass


# noinspection PyTypeChecker
def test_facebook_button():
    fb = Facebook()
    s = stack(FbButtonTemplate(
        'foo',
        [FbUrlButton('foo', 'https://example.com')]
    ))

    with patch.object(fb, '_send', return_value=instant_run()) as mock_send:
        run(fb.send(None, s))
        mock_send.assert_called_once_with(None, {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': 'foo',
                    'buttons': [
                        {
                            'type': 'web_url',
                            'title': 'foo',
                            'url': 'https://example.com'
                        },
                    ],
                },
            },
        })


# noinspection PyTypeChecker
def test_facebook_share():
    fb = Facebook()
    s = stack(FbButtonTemplate(
        'foo',
        [FbShareButton(FbGenericTemplate([
            FbCard(
                title='foo',
                subtitle='bar',
                buttons=[
                    FbUrlButton('baz', 'https://example.com'),
                ],
            ),
        ]))]
    ))

    with patch.object(fb, '_send', return_value=instant_run()) as mock_send:
        run(fb.send(None, s))
        mock_send.assert_called_once_with(None, {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': 'foo',
                    'buttons': [
                        {
                            'type': 'element_share',
                            'share_contents': {
                                'attachment': {
                                    'type': 'template',
                                    'payload': {
                                        'template_type': 'generic',
                                        'sharable': False,
                                        'elements': [
                                            {
                                                'title': 'foo',
                                                'subtitle': 'bar',
                                                'buttons': [
                                                    {
                                                        'type': 'web_url',
                                                        'title': 'baz',
                                                        'url': 'https://'
                                                               'example.com',
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                    ],
                },
            },
        })
