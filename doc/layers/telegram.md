Telegram Layers
===============

Well, Telegram has a lot of unique features in comparison of other
platforms. And not all of them are easy to understand or deal with.
Fortunately, the layers system allows use all of Telegram's features,
however it's not necessarily always straightforward.

## Inline keyboard and update

Inline keyboards are one of the most powerful features of Telegram bots.
However, their logic is a bit tricky and this part of the documentation
aims at explaining how to perform the different use cases using the
available layers.

### `InlineKeyboard`

This generates an
[inline keyboard](https://core.telegram.org/bots/api#inlinekeyboardmarkup),
which is a quite interesting feature of Telegram. It's kind of like
the Facebook quick replies, however it can lead to more actions.
Including open an URL and
[update their attached message](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating).

Usage:

```python
class FakeState(FakeAppState):
    async def handle(self):
        self.send(
            lyr.Text('Foo?'),
            tgr.InlineKeyboard([
                [tgr.InlineKeyboardUrlButton(
                    text='foo',
                    url=URL,
                    sign_webview=True,
                )],
                [tgr.InlineKeyboardCallbackButton(
                    text='foo',
                    payload={'action': 'foo'},
                )],
                [tgr.InlineKeyboardSwitchInlineQueryButton()],
                [tgr.InlineKeyboardSwitchInlineQueryCurrentChatButton()],
            ])
        )
```

You can see that the sole parameter of `InlineKeyboard` is a
2-dimensions array of buttons. The first dimension is rows and the
second one is columns.

There is 4 types of buttons:

- `InlineKeyboardUrlButton` opens an URL in a webview
    - `text` is the text on the button
    - `url` is the URL to open
    - `sign_webview` defaults to false, set to true in order to
      automatically append a token to the URL (to use with `bernard.js`)
- `InlineKeyboardCallbackButton` sends a message with a `Postback`
  layer containing the `payload`
    - `text` is the text displayed on the button
    - `payload` is a JSON-serializable payload (that will take less
      than 64 bytes!)
- `InlineKeyboardSwitchInlineQueryButton` starts an inline query with
  a friend
- `InlineKeyboardSwitchInlineQueryCurrentChatButton` starts an inline
  query in the current chat

### `AnswerCallbackQuery`

When the user clicks a `InlineKeyboardCallbackButton`, it creates
a **callback query**. While they have a role behind the scene, you can
also use them to:

- Display an alert popup
- Display a notification on top of the screen

The framework will automatically append the `AnswerCallbackQuery` layer
if needed, however you can override it by sending your own:

In `states.py`

```python
class TestState(MyAppState):
    async def handle(self) -> None:
        if self.request.has_layer(lyr.Postback):
            self.send(
                tgr.AnswerCallbackQuery(
                    text='It looks like you clicked',
                )
            )
        else:
            self.send(
                lyr.Text('You should click the button'),
                tgr.InlineKeyboard([[
                    tgr.InlineKeyboardCallbackButton(
                        text='Yeah, click me',
                        payload={'action': 'click'},
                    ),
                ]])
            )
```

In `transitions.py`

```python
# ...
    Tr(
        dest=TestState,
        factory=trg.Equal.builder(BotCommand('/test')),
    ),
    Tr(
        dest=TestState,
        factory=trg.Action.builder('click'),
    ),
# ...
```

You can type `/test` in  your bot, it will display a message with a
button. If you click the button, it will display a text as notification
on top of the screen.

Available options for `AnswerCallbackQuery` are:

- `text` text to be displayed
- `show_alert` if True, display as an alert popup, if False display as
  a notification on top.
- `cache_time` is the time to keep this answer in cache (default is 0)

### `Update`

When a callback button is clicked, you also have the opportunity to
update the attached message (aka the message right above the button).

In order to do this, simply put an `Update` layer at the end of your
stack.

To demonstrate this, let's do a click counter. It's simply a message
with an associated button that will count the number of times that you
click on that button.

In `states.py`

```python
class TestState(MyAppState):
    async def handle(self) -> None:
        try:
            # If the user clicked the button, there will be a `Postback` layer
            # with a counter attached to its payload. Here we try to read it.
            cnt = int(self.request.get_layer(lyr.Postback).payload['cnt'])
        except (KeyError, ValueError):
            # When the payload isn't found, we default to 0
            cnt = 0

            # The `update` variable holds the update layer if necessary and is
            # empty otherwise. Here it's empty.
            update = []
        else:
            # When the counter was successfully retrieved, it means that it's
            # an update and then we add the update layer
            update = [tgr.Update()]

        self.send(
            # Those are the regular layers sent anyways
            lyr.Text(f'You clicked {cnt} time{"" if cnt == 1 else "s"}'),
            tgr.InlineKeyboard([[
                tgr.InlineKeyboardCallbackButton(
                    text='Click me',
                    payload={
                        'action': 'click',
                        'cnt': cnt + 1,
                    },
                ),
            ]]),

            # And here goes the optional update
            *update,
        )
```

In `transitions.py`

```python
# ...
    Tr(
        dest=TestState,
        factory=trg.Equal.builder(BotCommand('/test')),
    ),
    Tr(
        dest=TestState,
        factory=trg.Action.builder('click'),
    ),
# ...
```

## Reply Keyboard

Besides the inline keyboards described above, there is also the
[reply keyboards](https://core.telegram.org/bots/api#replykeyboardmarkup).

### `ReplyKeyboard`

Creates a reply keyboard below the text bar.

```python
self.send(
    tgr.ReplyKeyboard(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False,
    )
)
```

Options are:

- `keyboard`: a 2-dimensions array of buttons. The first dimension
  is rows and the second one is columns.
- `resize_keyboard`: make the keyboard as small as possible (otherwise
  it will expand to take most of the screen regardless of the number of
  buttons)
- `one_time_keyboard`: makes the keyboard disappear with the first click
- `selective`: only displays the keyboard for the current user and not
  for other participants of the conversation

#### `KeyboardButton`

A standard keyboard button. When the user clicks it, they will send to
the chat the button's text as a regular text message.

```python
self.send(
    tgr.ReplyKeyboard(
        keyboard=[[tgr.KeyboardButton(
            text='Do stuff',
            choice='do_stuff',
            intent=its.DO_STUFF,
        )]],
        resize_keyboard=True,
        one_time_keyboard=False,
        selective=False,
    )
)
```

Options are:

- `text`: Text to be displayed
- `choice`: Slug to be recognized by the `Choice` trigger
- `intent`: Intent to provide alternative textes that would do the same
  action

#### `LocationKeyboardButton`

If the user clicks this button, they will be prompted to send their
location.

## Inline Messages

[Inline messages](https://core.telegram.org/bots/inline) are another big
deal within Telegram bots. They allow to invocate your bot directly from
the message bar without even having to talk to the bot. By example if
you talk to a friend and type `@imdb Back To The Future` it will propose
you to send to your friend a recap message about the movie.

In order to enable inline messages, you need to configure your bot to
accept them in @BotFather.

Also, you have to consider that inline queries will create temporary
conversations that work a bit differently than regular chat
conversations.

### `InlineQuery`

When the user starts writing `@your_bot query string` you will receive
an `InlineQuery` layer with `query string` attached.

You can simply create the following transition:

```python
Tr(dest=Inline, factory=triggers.Layer.builder(tgr.InlineQuery)),
```

### `AnswerInlineQuery`

This is the layer you'll use to answer an inline query. Any answer
should be a list of items.

```python
self.send(tgr.AnswerInlineQuery(
    results=results,
    cache_time=0,
    is_personnal=True,
))
```

Options are:

- `results` is the list of results (see below)
- `cache_time` is a duration in seconds of how long to cache those
  results for this query
- `is_personal` are those results specific to the person or can the
  cache be re-used for other people as well?

### Results

There is many kind of results you can use and not all of them are
implmented today.

All results are subclasses of `InlineQueryResult` and take two common
arguments to their constructor:

- `identifiers` is a dict of elements that are unique for this item. By
  example, if you're listing items which all have an ID, you can simply
  use `{'id': item.id}` as identifiers.
- `input_stack` is the stack of layers that Telegram will send for you
  when the user clicks on an item.

#### `InlineQueryResultArticle`

Creates a row with a square thumbnail on the left, a title and an
optional description.

Options:

- `title` title of the item
- `url` opitional link to the correspond item on your website
- `hide_url` if there's an URL, don't show it in the message
- `description` optional description to go below the title
- `thumb_url` URL to the result's thumb (preferrably a small image)
- `thumb_width` and `thumb_height` are the size of the thumbnail in px

## Other layers

### `Reply`

Telegram allows you to reply a message by quoting it. You can use
this layer to indicate that you want to reply to the currently analyzed
message.

```python
class BullshitState(MyAppState):
    async def handle(self) -> None:
        self.send(
            lyr.Text('That is bullshit'),
            tgr.Reply(),
        )
```

This creates a bot that will call bullshit on anything you say (damn
that bot is impolite).

### `BotCommand`

This layer cannot be sent but it can be received when the user sends
a command to the bot, like `/start`.

Usually, the best way to intercept those commands is to use the `Equals`
trigger, like this in `transitions.py`:

```python
# ...
Tr(
    dest=TestState,
    factory=trg.Equal.builder(BotCommand('/test')),
),
# ...
```
