from unittest.mock import patch

from bernard.layers import stack
from bernard.platforms.facebook.helpers import Card, ShareButton, UrlButton
from bernard.platforms.facebook.layers import ButtonTemplate, GenericTemplate
from bernard.platforms.facebook.platform import Facebook
from bernard.utils import run


async def instant_run():
    pass


# noinspection PyTypeChecker
def test_facebook_button():
    fb = Facebook()
    s = stack(ButtonTemplate("foo", [UrlButton("foo", "https://example.com")]))

    with patch.object(fb, "_send", return_value=instant_run()) as mock_send:
        run(fb.send(None, s))
        mock_send.assert_called_once_with(
            None,
            {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "foo",
                        "buttons": [
                            {
                                "type": "web_url",
                                "title": "foo",
                                "url": "https://example.com",
                            },
                        ],
                    },
                },
            },
            s,
        )


# noinspection PyTypeChecker
def test_facebook_share():
    fb = Facebook()
    s = stack(
        ButtonTemplate(
            "foo",
            [
                ShareButton(
                    GenericTemplate(
                        [
                            Card(
                                title="foo",
                                subtitle="bar",
                                buttons=[
                                    UrlButton("baz", "https://example.com"),
                                ],
                            ),
                        ]
                    )
                )
            ],
        )
    )

    with patch.object(fb, "_send", return_value=instant_run()) as mock_send:
        run(fb.send(None, s))
        mock_send.assert_called_once_with(
            None,
            {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": "foo",
                        "buttons": [
                            {
                                "type": "element_share",
                                "share_contents": {
                                    "attachment": {
                                        "type": "template",
                                        "payload": {
                                            "template_type": "generic",
                                            "sharable": False,
                                            "elements": [
                                                {
                                                    "title": "foo",
                                                    "subtitle": "bar",
                                                    "buttons": [
                                                        {
                                                            "type": "web_url",
                                                            "title": "baz",
                                                            "url": "https://"
                                                            "example.com",
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
            },
            s,
        )
