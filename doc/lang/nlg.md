Natural Language Generation
===========================

BERNARD's language system is designed to best fit the needs of a bot, in
comparison to what applications usually do. It allows:

- **Translation** - Different messages for different locales
- **Contextual variations** - Different messages depending on arbitrary
  criterion, like gender, time of the day, bot's mood, etc
- **Randomization** - For a single key, messages can be randomized. This
  can create variation in what the bot says
- **Parameters substitution** - You can insert placeholders in your
  translations, like `Hello, {name}!`. Moreover, parameters can be
  formatted on the fly
- **Extensible** - The system is split into well-defined parts that
  you can extend to match your needs

## Configuration

The first step to get your translations running is to configure it.
Let's move from an example derived from the default config and explain
it.

```python
I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('fr'), 'responses.csv'),
            'locale': 'fr',
            'flags': {
                1: {'gender': 'unknown'},
                2: {'gender': 'male'},
                3: {'gender': 'female'},
            },
        },
    },
]
```

The first element is:

```python3
'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
```

This is the name of the *loader* class. It has the responsibility of
reading translation values and feeding them into the internal
dictionary. If you want to load translations from an external service
or API, you can easily implement your own loader by respecting the
`BaseTranslationLoader` interface.

Afterwards comes the `params` destined to configure this loader
specifically.

```python
'file_path': path.join(i18n_root('fr'), 'responses.csv'),
```

Gives the path to the CSV file to be read. `i18n_root('fr')` is a
provided utility function to generate a path to `PROJECT_ROOT/i18n/fr`
and `responses.csv` is simply the file's name.

```python
'locale': 'fr',
```

Is a locale name. And finally:

```python
'flags': {
    1: {'gender': 'unknown'},
    2: {'gender': 'male'},
    3: {'gender': 'female'},
},
```

Adds meta-data to the CSV columns. The key is the 0-indexed column
number inside the CSV and the value is a dictionary of all flags you
want to associate to this column. In the present case, you can see it's
mapping genders to columns. Later this will help having different
accords in the sentence depending on if the person is a man or a woman.

### Putting several locales

You might have noticed that `I18N_TRANSLATION_LOADERS` is a list. All
the loaders will be called. A single loader might load all the locales
at once, however in the case of the CSV loader each file is associated
with one specific locale. For this reason, if you want several locales
you can do something like that:

```python
I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('fr'), 'responses.csv'),
            'locale': 'fr',
        },
    },
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'responses.csv'),
            'locale': 'en',
        },
    },
]
```

### Locale choosing

Locales are usually represented using one of those forms:

- `xx` (like `fr` or `en`)
- `xx_YY` (like `en_US` or `en_IN`)
- `xx-yy` (like `es-es` or `es-la`)

There, `xx` is the ISO 639-1 of the language while `yy` or `YY` is the
ISO Alpha-2 country code (except sometimes `LA` is used for "Latin
America" and is not actually an ISO code).

The system understands all those syntaxes, because different platforms
use different syntaxes.

To select the locale to use for a specific user, it works like this:

1. All available locales are listed
2. The user's locale is fetched from the platform
3. Each available locale gets a score:
    - 2 for language and country match
    - 1 for language match
    - 0 for no match
4. The first locale with a top score wins (**the order of locales
   declaration indicates their priority!**)

In pratice, suppose that available locales are `fr`, `en` and `en_US`.
Let's consider that the user has the following locales:

- `fr` gets matched with `fr`
- `en_UK` gets matched with `en`
- `en_US` gets matched with `en_US`
- `it` gets matched with `fr`

### Regional settings

*Side note*: the `_FR` or `_US` part indicates the *regional* settings.
It mostly changes the way numbers, times and so on ar represented. By
example:

```python
from babel.numbers import format_number

assert format_number(100000, locale='en_US') == '100,000'
assert format_number(100000, locale='en_IN') == '1,00,000'
```

In BERNARD, only the available locales are considered. So if you don't
provide `en_IN`, even somebody that comes to the bot with the `en_IN`
locale won't be able to see `en_IN`-localized numbers. This is for
consistency and predictability reasons. If you want to support all
variants of English without translating for each version of it, just
declare the same file with several locales, like this:

```python
I18N_TRANSLATION_LOADERS = [
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'responses.csv'),
            'locale': 'en_US',
        },
    },
    {
        'loader': 'bernard.i18n.loaders.CsvTranslationLoader',
        'params': {
            'file_path': path.join(i18n_root('en'), 'responses.csv'),
            'locale': 'en_IN',
        },
    },
]
```

While you can use standard Python formatting parameters in parameters
substitution, all BERNARD-provided filters will take in account the
user's regional settings and his current timezone if available.

This means that `The number is {x:number}` will get a decent format for
the regional settings and `The time is {now:format_datetime:H:mm}` will
display the current time in the user's time zone. More on formatting
later.

### CSV Format

#### Basics

The CSV format is pretty simple. By default it expects no headers and
two columns:

0. Column 0 has the keys. Keys should be valid Python variable names,
   otherwise you're getting yourself into useless trouble.
1. Column 1 is the matching values.

Of course you can change that using the `flags` parameter in order to
have more columns taken in account, just like explained above.

#### Key format

The key has a special syntax in order to allow for the several features
to exist.

##### Randomization

In order to randomize between values, just use the same key several
times:

```
TEXT,foo
TEXT,bar
TEXT,baz
```

##### Split

As explained below in "Usage", there is a possibility to hint at
separate bubbles

```
TEXT+1,Bubble 1
TEXT+2,Bubble 2
```

## Usage

### In layers

From a state, it is pretty straightforward:

```python
from bernard.i18n import translate as t

# ...

class DemoState(MyAppState):
    async def handle(self) -> None:
        # Sends a simple text message
        self.send(lyr.Text(t.TEXT_MESSAGE))

        # Sends a text message split accross bubbles
        self.send(lyr.MultiText(t.MULTI_BUBBLE_MESSAGE))

        # Sends a parametrized text message
        self.send(lyr.Text(t('TEXT_WITH_PARAM', foo='bar')))
```

Let's break it down.

First off, there is two way to invocate the translation system:

- `t.TRANS_KEY` is the simplest way, if you don't have any parameter
- `t('TRANS_KEY', param='value')` if you have one or more params

So what is the difference between `Text` and `MultiText`? Often, texts
are not done by the same person than the one coding the bot. Also, some
platforms like Messenger don't allow texts to be too long. So, instead
of manually breaking down the message into separate bubbles at the
moment at writing the code, there is a specific syntax explained above.
If the string is used in a `MultiText` it will be split into several
messages while if it is a `Text` all parts will be concatenated.

### Manual rendering

If you want to instantly render a translated string, you need to use
the `bernard.i18n.translator.render` function.

```python
async def render(
        text: TransText,
        request: Optional['Request'],
        multi_line=False) -> Union[Text, List[Text]]:
    """
    Render either a normal string either a string to translate into an actual
    string for the specified request.
    """
```

The fields are:

- `text` is the text to be rendered
- `request` is the optional request (which is essential to get
  information about the user)
- `multi_line` returns the translation split in several likes if enabled
  and if the splitting feature is used for this key

Example:

```python
# ...
foo = t.FOO
print(await render(foo, request))
```
