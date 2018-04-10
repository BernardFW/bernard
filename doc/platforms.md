Platforms
=========

Although you can provide your own platform, BERNARD provides compatibility for
several platforms. You will find here all the supported platforms and their
configuration options.

## Facebook Messenger

**Class**: `bernard.platforms.facebook.platform.Facebook`

**Example config**

```python
import json
from os import getenv
from urllib.parse import urlparse


def extract_domain(var_name, output):
    var = getenv(var_name)

    if var:
        p = urlparse(var)
        output.append(p.hostname)


def make_whitelist():
    out = []
    extract_domain('BERNARD_BASE_URL', out)
    return out


PLATFORMS = [
    {
        'class': 'bernard.platforms.facebook.platform.Facebook',
        'settings': [
            {
                'security_token': getenv('FB_SECURITY_TOKEN'),
                'app_secret': getenv('FB_APP_SECRET'),
                'page_id': getenv('FB_PAGE_ID'),
                'page_token': getenv('FB_PAGE_TOKEN'),
                'whitelist': make_whitelist(),
                'greeting': [
                    {
                        'locale': 'default',
                        'text': 'Hi {{user_first_name}}'
                    },
                ],
                'menu': [
                    {
                        'locale': 'default',
                        'call_to_actions': [
                            {
                                'type': 'postback',
                                'title': 'Foo',
                                'payload': json.dumps({'action': 'foo'}),
                            },
                            {
                                'type': 'postback',
                                'title': 'Bar',
                                'payload': json.dumps({'action': 'bar'}),
                            },
                        ],
                    },
                ]
            }
        ],
    },
]
```

Here the settings accept a list of objects which can each point to a different
page/app. For each object, the keys are:

- `security_token` - An arbitrary secure random token that Facebook will ask
  you to provide when hooking the bot.
- `app_secret` - The app secret, found in the app configuration page
- `page_id` - The ID of the Facebook page
- `page_token` - The page subscription token created in your app's admin
- `whitelist` - A list of whitelisted domain names. Domains that need to be
  whitelisted include:
    - The bot's domain
    - Pages that will use the JS Messenger SDK
    - Pages that will display a Checkbox Plugin
- `greeting` - Greeting page configuration. See
  [the FB doc](https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api/greeting)
  for syntax.
- `menu` - Contents of the menu. See
  [the FB doc](https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api/persistent-menu)
  for syntax.

Please note that only `security_token`, `app_secret`, `page_id` and
`page_token` are mandatory for the bot to work.

### Sending

Authorized message stacks are:

- **Text**: `(Text|RawText|MultiText)+ QuickRepliesList? MessagingType?`
- **[Generic Template](https://developers.facebook.com/docs/messenger-platform/send-messages/template/generic)**: `GenericTemplate QuickRepliesList? MessagingType?`
- **[Button Template](https://developers.facebook.com/docs/messenger-platform/send-messages/template/button)**: `ButtonTemplate QuickRepliesList? MessagingType?`
- **Attachment**: `(Image|Audio|Video|File) QuickRepliesList? MessagingType?`
- **Sleep**: `Sleep`
- **Typing**: `Typing`

### Receiving

Expected layers are:

- `RawText` (+ `QuickReply` if a quick reply was clicked)
- `Image`
- `Audio`
- `File`
- `Video`
- `Location`
- `Postback`
- `Optin`


## Telegram

**Class**: `bernard.platforms.telegram.platform.Telegram`

**Example config**

```python
PLATFORMS = [
    {
        'class': 'bernard.platforms.telegram.platform.Telegram',
        'settings': {
            'token': getenv('TELEGRAM_TOKEN'),
        }
    }
]
```

In order to create a Telegram bot and configure it, you need to talk
to `@BotFather`. He will also provide you with the token to be put in
`TELEGRAM_TOKEN`.

### Sending

Authorized message stacks are:

- **[Plain Text](https://core.telegram.org/bots/api#sendmessage)**: `(Text|RawText)+ (InlineKeyboard|ReplyKeyboard|ReplyKeyboardRemove)? Reply?|(Text|RawText) InlineKeyboard? Reply? Update`
- **[Markdown](https://core.telegram.org/bots/api#sendmessage)**: `Markdown+ (InlineKeyboard|ReplyKeyboard|ReplyKeyboardRemove)? Reply?|Markdown InlineKeyboard? Reply? Update`
- **[Inline Answer](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)**: `AnswerInlineQuery`
- **Sleep**: `Sleep`
- **Typing**: `Typing`

### Receiving

Expected layers are:

- `RawText`
- `BotCommand`
- `Message`
- `Image`
- `Postback`
- `InlineMessage`
- `InlineQuery`
