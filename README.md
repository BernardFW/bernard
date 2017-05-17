BERNARD
=======

Create powerful and flexible bots using BERNARD. Features (will) include:

- Represent conversations as finite-state machines
- Multi-platform (Facebook Messenger, WeChat, VK, Line, Twilio, ...)
- Flexible translation system. Handles language, plurals, gender and anything you'd like
- Run-time analysis through logging

BERNARD stands for "Bot Engine Responding Naturally At Requests Detection".

# Design goals

This framework does not exist yet. Here we'll list a few code snippets of how we want things to
look like from a developer standpoint.

## Introspection

Make it possible to easily create a graph of the FSM with a static analysis (which would allow
the creation of tools to automatically model a bot).

Each transition should also be annotated/documented.

## Story interface

Each state of the FSM will be represented by a class. The class will have as members/functions
all the tools you need to handle the message (the message itself, a way to reply, get the context,
get info about the user, ...).

```python
class BaseStory(Story):
    async def error(self):
        # Something went wrong while generating the response, that's a 500 error
        pass

    async def confused(self):
        # That's when the bot is confused and does not find anything to say
        pass

class MyStory(BaseStory):
    async def handle(self):
        # Produce the messages that this state is supposed to produce
        pass

    # MISSING = how do you do transitions?
```

## Transitions

Transitions can't be in the same instance as the story, since they are awoken to know if we need to
instantiate the story. However, transitions still need mostly what stories have (context, message,
user, and so on).

The idea is to make them a sub-class of another story with a conventional name. This sub-class will
be instantiated every time there is 

```python
transitions = [
    trans(origin=None, dest=HelloStory, factory=TextTransition.builder(intent='foo')),
    trans(origin=HelloStory, dest=YesStory, factory=ChoiceTransition.builder(when='yes')),
    trans(origin=HelloStory, dest=NoStory, factory=ChoiceTransition.builder(when='no')),
    trans(origin=None, dest=InsultStory, factory=TextTransition.builder(intent='insult'), 
          weight=0.6, desc="When the user becomes insulting"),
    trans(origin=InsultStory, dest=FuckYouStory, factory=AnyTransition.builder()),
]
```

We also need a register to store information related to the next transition. And that should come
from each layer. Which means that each layer can emit something for the `trans_register`.

The API of transitions would be something like

```python
class BaseTransition(object):
    def __init__(self, request):
        self.request = request

    @classmethod
    def builder(cls, *args, **kwargs):
        def factory(request):
            return cls(request, *args, **kwargs)
        return factory

    def rank(self) -> Optional[float]:
        """
        Given the current request, ranks on a scale from 0 to 1 how likely it is that this
        transition matches it.
        """
        raise NotImplementedError

    def patch(self) -> None:
        """
        This method will be called when the transition is selected. If you need to alter the request
        or the user context, this is where you need to do it.
        """
        pass

class TextTransition(BaseTransition):
    def __init__(self, request, intent):
        super(TextTransition, self).__init__(request)
        self.intent = intent

    def _compare_text(self, text):
        return 1  # implement the text matching logic here

    def rank(self):
        msg = self.request.message

        if msg.has_layer(layers.Text):
            return self._compare_text(msg.get_layer(layers.Text).text)
            
class ChoiceTransition(BaseTransition):
    def __init__(self, request, when=None):
        super(ChoiceTransition, self).__init__(request)
        self.when = when
        self.choice = None
        
    def _rank_choice(self, choice):
        return 1  # todo implement ranking logic
        
    def rank(self):
        choices = self.request.get_trans_register('choices', [])

        if not choices:
            return

        self.choice, score = max((x, self._rank_choice(x) for x in choices), key=lambda y: y[1])

        if score and (self.when is None or self.when == self.choice.slug):
            return score
```

## Global app

We should have a global app that gets instantiated like this:

```python
app = Bernard(config)
app.serve()
```

This will parse all the stuff, initialize what needs to be and so on.

## Intents DB

Intents DB is a list of words/phrases that the user might say in order to trigger a story. It should
be accessible easily from everywhere but also I don't see why it should be a singleton. The simplest
thing would be to tie it to the Sanic app.

## Message layering

Simply put, messages are composed of content layers. Each platform will support only specific
combinations of layers. Like:

- Everybody handles a single text layer
- Facebook might allow for text + quick replies
- VK has text + image whereas Facebook has not
- and so on

```python
from bernard import layers

class MyStory(BaseStory):
    async def handle(self):
        self.reply(layers.Text('Hello'))

        with self.alternate() as msg:
            msg(
                layers.Card(card1),
                layers.Card(card2),
                layers.Card(card3),
            )

            msg(
                layers.Image(image1),
                layers.Image(image2),
                layers.Image(image3),
            )
```

Here, two ways to send a message:

1. Use `self.reply()` which allows only one alternative to be sent. Do this if you know that all
   the platforms you support will handle your layer(s) correctly
2. Use `self.alternate()` context manager in order to propose alternative sets of layers. By
   default, platforms will accept layers only if they fully support them, however you can use
   middlewares to transform layers into other layers so you can emulate features that do not exist
   (or that exist differently).
   It will choose the best-matching set of layers and send only this one.

## Configuration

Configuration is composed of two things:

1. App-specific configuration (like the name of classes, list of middlewares, etc) that is commited
   and found in a Python file
2. Instance-specific configuration that comes from environment variables (like tokens and passwords)

Configuration works like in Django and can be imported in a `from bernard.config import settings`
fashion.

## Middlewares

Middlewares allow to automatically propose alternatives to layer sets.

Default middleware are defined at the app level in the configuration, however each story can
customize its middlewares.

```python
class MyStory(BaseStory):
    def get_middlewares(self):
        m = super(MyStory, self).get_middlewares()
        m.append(MyOtherMiddleware())
        return m
```

```python
from typing import Optional, Tuple, List, Iterable
from bernard.layers import Text, QuickReplies, QuickReply, BaseLayer
from bernard.i18n import translate as t, intents as i


def middleware_for(pattern):
    """
    That's a decorator that will check if the request matches a specific pattern.
    """
    raise NotImplementedError


class ConfirmationToQuickReplies(BaseMiddleware):
    @middleware_for('Confirmation')
    def filter_response(self, request, response) -> Optional[Tuple[List[BaseLayer], float]]:
        confirmation = response[0]
        filtered = [
            Text(confirmation.text),
            QuickReplies(
                QuickReply('yes', t.YES, i.YES),
                QuickReply('no', t.NO, i.NO),
            ),
        ]

        return filtered, 0.8

class QuickRepliesMock(BaseMiddleware):
    @middleware_for('Text+ QuickReplies')
    def filter_response(self, request, response) -> Optional[Tuple[List[BaseLayer], float]]:
        filtered = list(response)

        qr = response[-1]
        text = t('LIST_JOIN_OR', list=[x.text for x in qr.replies])
        filtered.append(TextLayer(text, trans_register=qr.trans_register))

        return filtered, 0.7

class Humanize(BaseMiddleware):
    @platform(['facebook'])
    def filter_batch(self, request, responses) -> Optional[List[List[BaseLayer]]]:
        out = []
        for response in responses:
            filtered = []
            for layer in response:
                if isinstance(layer, layers.TextLayer):
                    filtered.append(layers.TypingLayer(typing=on))
                    filtered.append(layers.SleepLayer(duration=1.0))
                filtered.append(layer)
            out.append(filtered)
        return out
```

Each middleware output is given to other middlewares until it gets accepted by the platform. (Is it
a good idea? I smell infinite recursion here. TODO decide how to mitigate that).

The goal of middlewares is not to make sure that contents fit within the platform limits. If a
message is too long, sending will be stopped and an error will be logged.

There is also the `filter_batch()` method which filters a batch of messages to add things like
typing indications. If the output is not accepted by the platform, then it is discarded.

## Translation

Instead of just depending on the language, the translation system allows to make translations vary
according to an arbitrary number of criterion.

You can use translations this way:

```python
from bernard.i18n import translate as t
from bernard import layers

class MyStory(BaseStory):
    async def handle(self):
        # Simple case
        self.reply(layers.Text(t.HELLO)) # simple form
        self.reply(layers.Text(t('HELLO'))) # verbose form

        # With plural
        self.reply(layers.Text(t('PLURALIZE', 42)))

        # With substitution
        self.reply(layers.Text(t('SUBSTITUTE_ME', foo='bar')))
        self.reply(layers.Text(t('SUBSTITUTE_ME_PLURALIZE', 42, foo='bar')))
```

The idea is that you can make vary the translation according to lang and gender, by example. You
could get something like that:

| Key                           | Male              | Female             | Unknown             |
| ----------------------------- | ----------------- | ------------------ | ------------------- |
| SUBSTITUTE_ME_PLURALIZE\[0,1] | {name} le grand   | {name} la grande   | {name} en grandeur  | 
| SUBSTITUTE_ME_PLURALIZE\[2,]  | {name} les grands | {name} les grandes | {name} en grandeurs | 
| HELLO                         |                   |                    | Bonjour             |
| RANDOM+1                      |                   |                    | Rand 1, Bubble 1    |
| RANDOM+1                      |                   |                    | Rand 1, Bubble 2    |
| RANDOM+2                      |                   |                    | Rand 2, Bubble 1    |
| RANDOM+2                      |                   |                    | Rand 2, Bubble 2    |
| RAND_PLUR\[0]+1               |                   |                    | Plural + random     |

Translated strings are not real strings but rather objects that you can render any time you'd like
using a context of your choosing. This will be done automatically by the layer-rendering functions
in the framework and other framework facilities.

The other option would be to have a magic Django `get_language()`-like function, but I don't like
magic and I feel it can be avoided here.

Python-side, we'll get an API that does two things:

- `.render()` which always produces a single merged string of everything (with `\n` between)
- `.render_list()` which produces a list of strings (even if there is only one) so that things like
  `layers.Text` can split that into several bubbles. 

The randomization system will work as follow:

- Messages are sorted using the "rand ID" in the key
- Current position for each key is stored in conversation context
- Initial position is calculated with a modulo on (conversation + key)'s hash.

## Translations configuration

Translations can be loaded from various sources. Those sources could refresh themselves, so the
translation database needs to be updatable via callbacks.

Loaders are listed and configured in the configuration file.

In order to configure dimensions, several things:

- The configuration file will provide the dimensions and their possible values
- The developer will also have to provide a function which given a request will return the according
  dimension values
- This means that the user object will have to be cached in order to avoid querying the platform all
  the time.
- Dimensions must be deduced from the conversation and not the user. Conversations auto-guess their
  language, however it is persisted in cache and they provide an API to change the current language.
- At some point, we'll have to talk to external libs like Babel. Given internal knowledge + app
  dimensions, the conversation must be able to generate a traditional `en_IN`-like string.

## Message templating

Templating is needed in a very basic form inside text translations. We'll use the Python string
formatting ability to do so. It allows to do things like:

```
Hello, {name}
```

There will be in the configuration a way to register filters, in order to get custom output. There
will be built-in filters as well. Such as:

```
Hello, {name}. You owe {amount:money}
```

Or

```python
# Given this template
FOO = 'Say: {options:joinor}'

# You could do
assert t('FOO', options=['yes', 'maybe', 'no']).render(i18n_context) == 'Say: yes, maybe or no'
```

## Media handling

Media handling is quite a pain in the ass. Messenger is pretty simple (just give any HTTPS URL),
however other platforms require you to upload the data in a more or less straightforward way.

Also, media might need to be resized or re-encoded for each specific platform.

This means that media handling should be done on a separate process/machine that will specialize
in resizing stuff.

Moreover, media provided by platforms are accessible for some time but don't stay online forever.
We need to store them somewhere if we care to keep them.

- Each platform has its media downloader/store module (which takes arbitrary JSON as input)
- For any media you can get an internal media ID
- Which you can use to generate thumbnails/cropped versions/and so on
- Then each platform can use the output to push the media online and use an opaque data structure
  to send to itself

## Logging

We'll use the Python 3 logging tools, as Sanic does. The configuration must be integrated.

## Single/Multi-user conversations

Although the main focus is 1:1 conversations, let's not set aside the possibility of group 
conversations too fast.

For each message, platform handlers will construct:

- A sender ID
- A conversation ID

We know that some provider do not allow yet group conversation although they will soon, so the
building of those ID has to be future-proof.

Those ID must also be short and textual, so they can be used as key, for indexing and so on. Also,
the ID space between sender/conversation and platforms must not overlap. Like `fb:single:12345` and
`fb:user:12345` for the conversation and the user.

The framework will maintain 2 contexts

- One for the conversation. It will store things like the state of the conversation or things
  related to a single user.
- One for the user. It can store user-specific preferences that will also be available in other
  conversations involving this user.
  
Now, how to access that in practice?

```python
async def handle(self):
    # Access user ID
    print(self.user.id)
    
    # Access conversation ID
    print(self.conversation.id)
    
    # Get user's friendly name
    print(await self.user.get_friendly_name())
    
    # Access conversation's context
    print(await self.conversation.context.get('some_key'))
    print(await self.conversation.context.set('some_key', {'some_json': True}, timeout=20 * 60))
```

## Context

The storing needs are:

- Current conversation status
- Persistent user and conversation contexts
- Duplicate messages and nonces

Which are two different access patterns. Let's say that we have 2 interfaces, one for each.

Configuration would look like this

```python
from os import getenv

REGISTER_STORE = {
    'class': 'bernard.stores.engines.RedisRegister',
    'url': getenv('BERNARD_REDIS_URL'),
}

NONCE_STORE = {
    'class': 'bernard.stores.engines.RedisNonce',
    'url': getenv('BERNARD_REDIS_URL'),
}

CONTEXT_STORE = {
    'class': 'bernard.stores.engines.PostgreSqlContext',
    'url': getenv('BERNARD_PSQL_URL'),
}
```

Then using the stores would be like

```python
from bernard.stores import register, nonce, context

# Register
await register.get(conversation_id)
await register.set(conversation_id, content)

# Nonce
await nonce.is_duplicate(message.nonce, max_time_delta=3600)

# Context
ctx = context.get(conversation_id)
```

## Typing indications

That's a special layer, `layers.Typing`

## Pause between messages

That's a special layer, `layers.Sleep`

## Send a message from a cron/external trigger

There will be an authenticated API endpoint that crons and external scripts will be able to call in
order to generate fake postback messages.

Each platform will expose a way to serialize a responder that can be re-created on the fly through
some specific logic.

Calling this API will require two arguments (besides the signature protocol):

- The serialized responder
- The payload to put in the postback message

## Read message trigger

For platforms that support read message detection, layers will all embed a `read_payload` parameter
that will come back inside a special layer if the layer ever gets read.

## Dead man switch

Each platform will have the freedom to implement a way to know if webviews get closed, and trigger
the appropriate layer.
 
## State redirection

If a handler returns the class of another state, then the engine will immediately transition to this
state.

## Multiple instances in the same process

Suppose that you have several FB pages for several languages. We need to both accept messages from
those pages and display the right lang.

```python
FACEBOOK = [
    {
        'page_id': '11111',
        'i18n_hint': {'lang': 'fr'},
    },
    {
        'page_id': '22222',
        'i18n_hint': {'lang': 'en'},
    },
]
```
