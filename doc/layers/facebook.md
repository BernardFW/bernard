Facebook Layers
===============

Facebook has quite unique concepts, especially like "quick replies" and
"generic templates".

Not all options of all layer is described here, you can have a look
at each layer's embedded documentation.

## `MessagingType`

This special Facebook layer indicates to Facebook the cause of the
message. It's particularly useful when you send a notification. By
default a "response" type is set, however you must set it to something
else if you're doing something else :)

See [Facebook's documentation](https://developers.facebook.com/docs/messenger-platform/send-messages#messaging_types).

```python
class FakeState1(FakeAppState):
    async def handle(self):
        self.send(
            lyr.Text(t.WELCOME),
            fbl.MessagingType(response=True),
        )

class FakeState2(FakeAppState):
    async def handle(self):
        self.send(
            lyr.Text(t.NEW_VERSION),
            fbl.MessagingType(tag=fbl.MessageTag.APPLICATION_UPDATE),
        )
```

## `QuickRepliesList`

This sends a list of
[quick replies](https://developers.facebook.com/docs/messenger-platform/send-messages/quick-replies).
You can send up to 11 of them.

From the [Number Bot](../get-started/number-bot.md):

```python
class S001xWelcome(NumberBotState):
    """
    Welcome the user
    """

    @page_view('/bot/welcome')
    async def handle(self) -> None:
        name = await self.request.user.get_friendly_name()

        self.send(
            lyr.Text(t('WELCOME', name=name)),
            fbl.QuickRepliesList([
                fbl.QuickRepliesList.TextOption(
                    slug='play',
                    text=t.LETS_PLAY,
                    intent=its.LETS_PLAY,
                ),
            ]),
        )
```

Please note that there is two options you can use:

- `QuickRepliesList.TextOption(slug, text, intent)` displays a text.
  When the user clicks, the `Choice` trigger can detect the `slug`. The
  `intent` is here to allow the user to type actual text instead of
  clicking. This parametter is nullable.
- `QuickRepliesList.LocationOption()` displays a button that the user
  can click to share his location. There is no control over the wording
  or look of it.

## `QuickReply`

When the user has clicked a quick reply, this layer will be present in
the stack. However it's not recommended to use it directly, as you
should rather let the `Choice` trigger do the work. If you want to
know which choice was made from the state, you can do code like this:

```python
class FakeState(FakeAppState):
    async def handle(self):
        assert isinstance(self.trigger, Choice)
        chosen = self.trigger.slug
```

## `ButtonTemplate`

Sends a [Button Template](https://developers.facebook.com/docs/messenger-platform/reference/template/button).

```python
from bernard.platforms.facebook import helpers as fbh, layers as fbl

class Connection(BaseFakeState):
    """
    Present the user with choices for connecting/creating an account
    """

    @page_view('/bot/connect/start')
    async def handle(self) -> None:
        self.send(fbl.ButtonTemplate(
            text=t.ASK_CREATE_ACCOUNT,
            buttons=[
                fbh.UrlButton(
                    title=t.I_CONNECT,
                    messenger_extensions=True,
                    url=CONNECT_URL,
                    webview_height_ratio=FbWebviewRatio.tall,
                ),
                fbh.UrlButton(
                    title=t.I_CREATE,
                    messenger_extensions=True,
                    url=CREATE_URL,
                    webview_height_ratio=FbWebviewRatio.tall,
                ),
                fbh.PostbackButton(
                    title=t.I_SKIP,
                    payload={'action': 'skip_link'},
                ),
            ],
        ))
```

## `GenericTemplate`

Sends a [Generic Template](https://developers.facebook.com/docs/messenger-platform/reference/template/generic).
This is by far the most complex template to setup.

```python
from bernard.platforms.facebook import helpers as fbh, layers as fbl

class FakeState(FakeAppState):
    async def handle(self):
        cards = []

        for i in range(5):
            cards.append(fbh.Card(
                title=f'Card #{i + 1}',
                buttons=[
                    fbh.PostbackButton(
                        title=t.DO_STUFF,
                        payload={
                            'action': 'skip_link',
                            'card_id': i,
                        },
                    ),
                ],
            ))

        self.send(fbl.GenericTemplate(cards))
```

## `OptIn`

When the user does an opt-in, like when they click on a
"Send to Messenger" button.
