Natural Language Understanding
==============================

There has been a huge effort to try to modelize the human speech,
however most attempts failed because the human grammar makes basically
no sense and is full of exception. Not to mention the fact that the
actual meaning of the words matters in order to understand the actual
grammatical structure of a stencence.

So, until we have computers able to understand every human concept and
thus understand human speech, we need to use tricks to look like we
understand what the person says.

The first issue with natural language understanding is that you can't
give people a blank text input with no directions. They know that the
bot won't be able to understand everything but they don't know what the
bot understands. If you want people to use your NLU, you mostly need
to teach them how it works.

Also, you need to restrict the context as much as possible. If the
expected questions only target a very specific topic, it's easier to
imagine what could be asked.

## Options

General advice aside, BERNARD comes with its own very simple solution
for NLU. There is also the possibility to plug in an external NLU
engine.

- BERNARD-powered
    - Built-in NLU (explained below)
    - [Iron Throne](https://github.com/BernardFW/iron-throne)
- DIY options
    - [rasa NLU](https://nlu.rasa.com/)
- SaaS
    - [wit.ai](https://wit.ai)
    - [dialogflow](https://dialogflow.com)
    - [LUIS](https://www.luis.ai/)
    - [Amazon Lex](https://aws.amazon.com/lex/)

While BERNARD provide its own NLU solutions for practical reasons, it's
at the outer limit of the scope. The main problem that BERNARD solves is
simply the logistics of connecting your bot to different platforms and
managing the state machine. All other NLU solutions have good and bad
sides, so it's up to you to choose.

A few pointers:

- How much time do you have to undestand the thoery behind and setup
  the service?
- Is there a pricing offer that is compatible with your requirements?
- Are you okay with leaking all your data to a GAFAM?
- Do you trust the provider not to change its offer (increase the
  pricing overnight? close the service?)

## Built-in NLU

The built-in system is there to facilitate several situations and help
you build basic NLU. It is by no means complete and there is many
things that you cannot accomplish with it.

### Core concepts

This system works with *intent detection*.

1. You define a list of intents ("go to next step", "get an update",
   ...)
2. For each intent, you define a list of sentences that can trigger that
   intent

Please note that there is no support for *entities*. It means that you
can detect something like `How are you today?` but you can't detect
`What is the weather in Madrid?` and extract "Madrid".

### Algorithm

The built-in system is pretty simple, since it's based on
[trigrams](https://en.wikipedia.org/wiki/Trigram). Basically, it's based
on the algorithms behind PostgreSQL's
[pg_trgm](https://www.postgresql.org/docs/current/static/pgtrgm.html)
module.

More specifically, it works like this:

1. You write down all the possible sentences for all the possible
   intents
2. The user submits a text message
3. The message will get normalized
    - Lowercase
    - Accents stripped
    - Transform any punctuation into space
    - Merge all joined spaces
4. It is compared with all known sentences
5. Only the best match is kept
6. If similarity is high enough, it's considered to be a match

#### Negative matches

If you configure it, you can enable negative matches. Suppose that you
have a `THANK_YOU` intent that accepts the `thanks` sentence. If the
user says `no thanks` it will still be a close match and will probably
trigger the `THANK_YOU` intent even though the user meant the opposite.

That is why there is an option to add negative intents, that will cancel
the first intent. In the case of `THANK_YOU`, you can put `thanks` as
sentence and `no thanks` as negative sentence.

### Configuration

Let's take something derived from the default config:

```python
I18N_INTENTS_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvIntentsLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'intents.csv'),
            'locale': 'en',
            'key': 0,
            'pos': 1,
            'neg': [(2, None)],
        },
    },
]
```

Breaking this down:

- `file_path` is the path to the source CSV file
- `locale` is the locale of those intents
- `key` indicates the column with the intent's key (like `THANK_YOU`)
- `pos` indicates where is the column with the sentence
- `neg` indicates the column(s) where are the negative intents

Those are the default values, if you don't want to change then, you only
have to set `file_path` and `locale`.

### CSV format

As you've seen in the configuration, you can set which column does
what. However, here is an example:

```csv
HELLO,hi,,
HELLO,hello,,
HELLO,howdy,,
THANK_YOU,thank you,no thank you,no thanks
THANK_YOU,thanks,no thanks,no thank you
```

As you can see, the number of filled columns varies depending on how
many negative intents you have to put.

- Column 0 has the keys. A single key can be repeated as many times as
  you'd like
- Column 1 has the sentences.
- Columns 2 and more have the negative sentences

### Usage

Intents can be used from transitions and from some layers.

#### Transitions

By example, let's define a transition when the user asks "What can you
do?"

Your `intents.csv` file should look like this:

```csv
WHAT_CAN_YOU_DO,what can you do?
WHAT_CAN_YOU_DO,what do you know?
WHAT_CAN_YOU_DO,what's your job?
WHAT_CAN_YOU_DO,do something!
```

Then in your `transitions.py` file:

```python
from bernard.i18n import intents as its
from .states import ExplainWhatCanDo

# ...

transitions = [
    Tr(
        dest=ExplainWhatCanDo,
        factory=trg.Text.builder(its.WHAT_CAN_YOU_DO),
    ),

    # ...
]
```

#### Layers

Some layers can rely on intents to help moving forward. By example,
quick replies (which rely on the `Choice` trigger) will use intents
to detect if the user typed something close to one of the options.

By example, from the number bot:

```python
class S004xCongrats(NumberBotState):
    """
    Congratulate the user for finding the number and propose to find another
    one.
    """

    @page_view('/bot/congrats')
    async def handle(self) -> None:
        self.send(
            lyr.Text(t.CONGRATULATIONS),
            fbl.QuickRepliesList([
                fbl.QuickRepliesList.TextOption(
                    slug='again',
                    text=t.PLAY_AGAIN,
                    intent=its.PLAY_AGAIN,
                ),
            ]),
        )
```

You can see here the `intent=its.PLAY_AGAIN` part. It means that if
instead of clicking "Play again" the user prefers to type "play again"
or "another round", it will be detected correctly (if the intent has
the right sentences of course).
