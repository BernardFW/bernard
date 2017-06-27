Get Started
===========

This part of the doc will guide you through understanding the basics of how
Bernard works.

A good starting point is the [demobot](../demobot). In this documentation,
we'll go through the code of the bot and then we'll dig into the more
theoretical concepts.

It is a Facebook Messenger bot, which means that you'll only be able to talk
to it through Facebook and you'll need to setup a bot on their platform.

**TLDR**: I'm sorry, this page is as short as I can imagine it, you'll have to
read it all. No one-liner to start, that's a framework built for the real
world.

## Base code

The core of the bot is in two files:

- [`states.py`](../demobot/states.py) has the code of the bot for each state,
  that's basically the code that drives what the bot does
- [`transitions.py`](../demobot/transitions.py) lists the transitions between
  states. That's how you describe the user flow.

Other files are present for technical reasons:

- [`settings.py`](../demobot/settings.py) are simply the settings, which
  covers pretty much everything from the API tokens to any single timeout. To
  start a project, you only need to fill a few variables.
- [`__init__.py`](../demobot/__init__.py) makes the folder into a Python
  module, it's ok if it's empty.
- Language files. Those are subject to serious changes in the future, as
  currently the translation system is far from being feature-complete.
    - [`i18n/fr/intents.csv`](../demobot/i18n/fr/intents.csv) are the intents,
      or rather the list of sentences the user might say to trigger a specific
      intent. More on that later.
    - [`i18n/fr/responses.csv`](../demobot/i18n/responses.csv) are the
      response strings we'll send to the user.

### Specs

This bot can be specified with the following diagram:

![demobot flow](https://cdn.rawgit.com/BernardFW/bernard/develop/doc/fsm-hello.svg)

Read it this way:

- The user can type the text "Hello" at any time. This will trigger the "Hello"
  state.
- The "Hello" state provides two quick replies (_"QR"_) to the user: "Yes" and
  "No". The user can click either of them.
- If the user chooses "Yes", the bot transitions to "Good".
- if the user chooses "No", the bot transitions to "TooBad".

Basically, it would look like:

- **User**: Hello
- **Bot**: Hello, are you all right?
- **User**: No
- **Bot**: That's your problem

As you can understand, you can trigger the "Hello" state from anywhere but you
can't go to "Good" if you're not on "Hello".

### Core files

As those files are the core of the bot, let's start with them.

#### `states.py`

Your bot needs a _base state_. This states defines the default behaviour of
your bot: what will it say when it does not understand user input or when
there is an internal error?

```python
from bernard.engine import BaseState
from bernard import layers as lyr
from bernard.i18n import translate as t, intents

class BaseTestState(BaseState):
    async def error(self) -> None:
        """Triggered when there is an internal error"""
        self.send(lyr.Text(t.ERROR))

    async def confused(self) -> None:
        """Triggered when the bot does not understand what the user says"""
        self.send(lyr.Text(t.CONFUSED))

    async def handle(self) -> None:
        raise NotImplementedError
```

As you can see, `error()` and `confused()` are implemented while `handle()` is
left to child classes. Indeed, the idea of this base state is that children
will be able to override its behaviour.

##### Your first state

Next, we'll define the "Hello" state.

```python
class Hello(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.HELLO))
        self.send(
            lyr.Text(t.HOW_ARE_YOU),
            lyr.QuickRepliesList([
                lyr.QuickRepliesList.TextOption('yes', t.YES, intents.YES),
                lyr.QuickRepliesList.TextOption('no', t.NO, intents.NO),
            ]),
        )
```

Let's break this down. First of all, you can see that everything happens in the
`handle()` function. This function gets called whenever the state is activated.
The function is `async`, which is part of Python's new
[asyncio](https://docs.python.org/3/library/asyncio.html) syntax/architecture.
If you are not familiar with it, you might want to dig into it. However, to
produce a simple working bot you don't need to understand how it works. Just
keep in mind to mark the function as `async` and you'll be fine.

You can also notice that `Hello` is a child of `BaseTestState`, the base state
that we defined earlier.

##### How messages are made

Next, we have the calls to `send()`. As one would expect, this function sends
a message to the user. Let's see the simplest one:

```python
self.send(lyr.Text(t.HELLO))
```

Part by part:

- `t.HELLO` is a way to get the translation from `responses.csv`.
- `lyr.Text()` creates a _text layer_ (which produces a text message).
- `self.send()` adds the message to the send list.

Wait, what the fuck is a layer? One of the main goals in Bernard is to provide
an abstraction layer above messaging platforms. In order to facilitate that,
it uses the concept of *layer*. Each message is composed of several layers, and
depending on the layers you use it will generate a different kind of message in
the target platform. This becomes obvious with the second message:

```python
self.send(
    lyr.Text(t.HOW_ARE_YOU),
    lyr.QuickRepliesList([
        lyr.QuickRepliesList.TextOption('yes', t.YES, intents.YES),
        lyr.QuickRepliesList.TextOption('no', t.NO, intents.NO),
    ]),
)
```

Break down:

- `lyr.Text(t.HOW_ARE_YOU)` is the text layer
- `lyr.QuickRepliesList([...])` is the quick replies layer
    - `lyr.QuickRepliesList.TextOption('yes', t.YES, intents.YES)` is the
      "Yes" quick reply
    - `lyr.QuickRepliesList.TextOption('no', t.NO, intents.NO)` is the "No"
      quick reply

You might wonder what `intents.YES` is. It's just a way to fetch the intents
list from `intents.csv`. We'll cover it later.

As you can see, with the layers model we can embed with the *text* message a
list of
*[quick replies](https://developers.facebook.com/docs/messenger-platform/send-api-reference/quick-replies)*.

_One last thing_: messages are **not** sent instantly. Instead, they are queued
to be sent right after the handler completes.

##### Latest states

With what we know now, the two last states are trivial to make:

```python
class Great(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.GREAT))


class TooBad(BaseTestState):
    async def handle(self):
        self.send(lyr.Text(t.TOO_BAD))
```

They are simply sending the `GREAT` or `TOO_BAD` message.

#### `transitions.py`

This files describes the possible transitions between states. It looks like
this:

```python
from bernard.engine import Tr, triggers
from bernard.i18n import intents
from .states import Hello, Great, TooBad

transitions = [
    Tr(Hello, triggers.Text.builder(intents.HELLO)),
    Tr(Great, triggers.Choice.builder(when='yes'), Hello),
    Tr(TooBad, triggers.Choice.builder(when='no'), Hello),
]
```

As you can see, we import the states from the other file. This is important.
The transitions **must** be in the `transitions` variable, that's where
BERNARD will look for them.

Basically, the `Tr()` object is a transition. It has multiple arguments but
let's go through only the 3 firsts:

- `dest` is the destination state
- `factory` is the trigger
- `origin` is the origin state. If you origin state is specified, then this
  transition can be triggered from any originating state

But what is a trigger? When a message comes in, we need to know which
transition it will activate. In order to do that, each transition has a
*trigger*. Each trigger will be polled and will reply with a probability of
the message being interesting for it.

Let's look at specific code lines to understand better:

```python
Tr(Hello, triggers.Text.builder(intents.HELLO)),
```

If the message has a text layer which matches the `HELLO` intent, then
transition to `Hello`.

Another one:

```python
Tr(Great, triggers.Choice.builder(when='yes'), Hello),
```

If the user comes from `Hello` and chose `yes` (probably in a quick reply) then
transition to `Great`.

## Running your bot

Now that you understand the core code of the bot, we'll get it running.

### Setup Python

BERNARD's architecture relies on Python features that are very recent. Because
of that, it requires _at least_ Python 3.6 (or more recent).

In order to have a development environment that is easy to manage, it is
recommended to have a virtual environment. Setting it up is outside the scope,
however you can have a look there:

- Linux/OSX: you can use [pyenv](https://github.com/pyenv/pyenv-installer)
- Windows: you can follow
  [this tutorial](http://timmyreilly.azurewebsites.net/python-pip-virtualenv-installation-on-windows/)
  and then
  [this one](http://timmyreilly.azurewebsites.net/setup-a-virtualenv-for-python-3-on-windows/)

In order to write code, the author recommends to use
[PyCharm Community](https://www.jetbrains.com/pycharm/download/#section=linux),
which is a really powerful editor. In any case, you should configure your IDE
to use the virtualenv you created.

### Install Bernard

Finally, when your environment is set, you can install Bernard. You can simply
do this with Pip:

```console
$ pip install bernard
```

### Setup environment

The first thing to do is to copy the [demobot](../demobot) file into a new
directory, which will be your project. To help you download it, there is a
[**downloadable tarball**](../demobot.tar.gz).

Suppose that you store your development projects in `~/dev`, then you can run

```console
$ curl https://raw.githubusercontent.com/BernardFW/bernard/develop/demobot.tar.gz | tar -C /tmp -x -z
$ mv /tmp/demobot ~/dev/mybot
```

### Configuration

You'll find the configuration in [`settings.py`](../demobot/settings.py). You
can use it as a boilerplate for your future bots. In this version, it reads
the configuration from environment variables. You have two choices: either
define the right environment variables (using your IDE, your process
management system, ...) or if you prefer you can just write your configuration
values right into the file.

#### Configuring your FB app

That's not the easiest part, but that's also outside the scope of this
tutorial. Roughly, if you want to setup a Facebook bot:

1. You need to create
   [a Facebook page](https://www.facebook.com/pages/create/).
2. You also need to create
   [a Facebook app](https://developers.facebook.com/).
3. In the app dashboard, go to the "Messenger" platform and then generate a
   token for your page.

That's the basic setup. The next step will be to connect the webhook, but you
are not ready for that.

#### Environment variables

Just a few environment variables are sufficient:

- `FB_SECURITY_TOKEN`: that's an arbitrary string that you will have to provide
  to Facebook. You can put _anything_ you want here but make sure it's long and
  secure.
- `FB_APP_SECRET`: this is the app secret which you can also find on your
  app's main page dashboard
- `FB_PAGE_ID`: the ID of your page (you can find it in the page's URL)
- `FB_PAGE_TOKEN`: this is the (quite long) token that you generated in the
  app dashboard

If you want to hardcode those variables, then replace the `getenv()` calls by
the value you want. In thise case, make sure not to commit the file to `git`,
of course.

#### Module names

You'll see a few occurrences of `demobot` in the `settings.py` file, you need
to replace them by the name of your bot (if you followed the example, it's
`mybot`).

#### Running the bot

BERNARD comes with a CLI `bernard` tool. It depends on the
`BERNARD_SETTINGS_FILE` environment variable to know where the configuration
is located. To run the server:

```console
$ cd ~/dev/mybot
$ BERNARD_SETTINGS_FILE=./settings.py bernard run
```

If all goes well, the bot should start right now. However you still need to
connect it to Facebook in order to use it.

#### Connecting to Facebook

In order to connect your bot to Facebook, you'll need to provide a webhook
URL. It's an URL that Facebook will call every time that you receive a message.

##### Creating a tunnel

The problem when you develop on your local machine is that it's pretty hard
to get a public URL. The easiest solution is to use a service like
[ngrok](https://ngrok.com/).

If you chose to use it:

```console
$ ngrok http 8666
```

##### Configuring Facebook

You need to go back to your app dashboard and to configure the webhook. To do
so, go to the "Messenger" section of your app, down to the "Webhook" and then
give an address like:

```
https://domain.of.your.bot/hooks/facebook
```

With `domain.of.your.bot` being the domain of your bot, by example the one that
was assigned to you by `ngrok`.

It will also ask you for a token. Give the value that you set to
`FB_SECURITY_TOKEN`.

And it will ask you to choose the events you want. Choose `messages` and
`messaging_postbacks`.

Once you validate, it should send a test request to your bot (you can see it
in the bot console) and then tell you that all is fine.

After that, you just need to subscribe your app to your page to receive events.

#### Talking to the bot

Now you're finally ready to talk to the bot. In order to do that you'll need
to go to `https://m.me/YOUR_PAGE_ID`.

## What next

So far, not much. You can read the
[unfinished old version of the get started](./get_started_old.md). It explores
more concepts (although unfinished).
