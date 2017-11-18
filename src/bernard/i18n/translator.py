# coding: utf-8
import re
from typing import List, Text, Optional, Dict, TYPE_CHECKING, Union, Tuple
from collections import Mapping, OrderedDict
from bernard.conf import settings
from bernard.utils import import_class, run
from string import Formatter
from .loaders import BaseTranslationLoader
from ._formatter import I18nFormatter

if TYPE_CHECKING:
    from bernard.engine.request import Request


class TranslationError(Exception):
    """
    That is the base translation error class
    """


class MissingTranslationError(TranslationError):
    """
    Raised when a translation that was asked does not exist
    """


class MissingParamError(TranslationError):
    """
    Raised if a translation needs parameters that can't be found
    """


def split_locale(locale: Text) -> Tuple[Text, Optional[Text]]:
    """
    Decompose the locale into a normalized tuple.

    The first item is the locale (as lowercase letters) while the second item
    is either the country as lower case either None if no country was supplied.
    """

    items = re.split(r'[_\-]', locale.lower(), 1)

    try:
        return items[0], items[1]
    except IndexError:
        return items[0], None


def compare_locales(a, b):
    """
    Compares two locales to find the level of compatibility

    :param a: First locale
    :param b: Second locale
    :return: 2 full match, 1 lang match, 0 no match
    """

    if a is None or b is None:
        if a == b:
            return 2
        else:
            return 0

    a = split_locale(a)
    b = split_locale(b)

    if a == b:
        return 2
    elif a[0] == b[0]:
        return 1
    else:
        return 0


class WordDictionary(object):
    """
    That's where the actual translation happens. It stores all translations in
    memory, puts the parameters in place and so on.
    """

    def __init__(self):
        self.dict = OrderedDict()
        self.loaders = []  # type: List[BaseTranslationLoader]
        self._init_loaders()
        self._choice_cache = {}

    def _init_loaders(self) -> None:
        """
        This creates the loaders instances and subscribes to their updates.
        """

        for loader in settings.I18N_TRANSLATION_LOADERS:
            loader_class = import_class(loader['loader'])
            instance = loader_class()
            instance.on_update(self.update)
            run(instance.load(**loader['params']))

    def update(self, new_data: Dict[Text, Dict[Text, Text]]):
        """
        Receive an update from a loader.

        :param new_data: New translation data from the loader
        """

        for locale, data in new_data.items():
            if locale not in self.dict:
                self.dict[locale] = {}

            self.dict[locale].update(data)

    def list_locales(self) -> List[Optional[Text]]:
        """
        Returns the list of available locales. The first locale is the default
        locale to be used. If no locales are known, then `None` will be the
        first item.
        """

        locales = list(self.dict.keys())

        if not locales:
            locales.append(None)

        return locales

    def choose_locale(self, locale: Text) -> Text:
        """
        Returns the best matching locale in what is available.

        :param locale: Locale to match
        :return: Locale to use
        """

        if locale not in self._choice_cache:
            locales = self.list_locales()

            best_choice = locales[0]
            best_level = 0

            for candidate in locales:
                cmp = compare_locales(locale, candidate)

                if cmp > best_level:
                    best_choice = candidate
                    best_level = cmp

            self._choice_cache[locale] = best_choice

        return self._choice_cache[locale]

    def get(self,
            key: Text,
            count: Optional[int]=None,
            formatter: Formatter=None,
            locale: Text=None,
            **params) -> Text:
        """
        Get the appropriate translation given the specified parameters.

        :param key: Translation key
        :param count: Count for plurals
        :param formatter: Optional string formatter to use
        :param locale: Prefered locale to get the string from
        :param params: Params to be substituted
        """

        if count is not None:
            raise TranslationError('Count parameter is not supported yet')

        locale = self.choose_locale(locale)

        try:
            out = self.dict[locale][key]
        except KeyError:
            raise MissingTranslationError('Translation "{}" does not exist'
                                          .format(key))

        try:
            if not formatter:
                out = out.format(**params)
            else:
                out = formatter.format(out, **params)
        except KeyError as e:
            raise MissingParamError(
                'Parameter "{}" missing to translate "{}"'
                .format(e.args[0], key)
            )

        return out


class StringToTranslate(object):
    """
    That's a string to translate. It holds the parameters until it gets
    rendered.
    """

    LINE_SEPARATOR = '\n'

    def __init__(self,
                 wd: WordDictionary,
                 key: Text,
                 count: Optional[int]=None,
                 **params):
        self.wd = wd
        self.key = key
        self.count = count
        self.params = params

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.key == other.key and
                self.count == other.count and
                self.params == other.params)

    def __repr__(self):
        parts = [repr(self.key)]

        if self.count is not None:
            parts.append(repr(self.count))

        for k, v in self.params.items():
            parts.append('{}={}'.format(k, repr(v)))

        return 't({})'.format(', '.join(parts))

    async def render(self, request=None):
        """
        Render the translation for the specified request. If no request is
        specified, do as good as possible.

        :param request: Bot request. No one knows what it's going to look like
                        so far.
        """

        return self.LINE_SEPARATOR.join(await self.render_list(request))

    # noinspection PyUnusedLocal
    async def render_list(self, request=None) -> List[Text]:
        """
        Render the translation as a list if there is multiple strings for this
        single key.

        :param request: Bot request.
        """

        if request:
            tz = await request.user.get_timezone()
            locale = await request.get_locale()
        else:
            tz = None
            locale = self.wd.list_locales()[0]

        f = I18nFormatter(locale, tz)
        return [self.wd.get(self.key, self.count, f, locale, **self.params)]


class Translator(object):
    """
    That's the basic object that you use to produce translations.
    """

    def __init__(self, wd: Optional[WordDictionary]=None):
        """
        We need the word dictionary here in order to pass it to the string to
        translate when it will get rendered.

        :param wd: a configured WordDictionary
        """

        self.wd = wd  # type: WordDictionary

        if not self.wd:
            self._regenerate_word_dict()

    def _regenerate_word_dict(self):
        """
        Re-generate the word dict, if you need to.
        """

        self.wd = WordDictionary()

    def __getattr__(self, key: Text) -> StringToTranslate:
        """
        Allow the `t.FOO` style.

        :param key: Key to get
        """

        return self(key)

    def __call__(self, key: Text, count: Optional[int]=None, **params) \
            -> StringToTranslate:
        """
        Allow the `t('FOO')` style.

        :param key: Key to translate
        :param count: Count for plurals
        :param params: Params to substitute
        """

        return StringToTranslate(self.wd, key, count, **params)


TransText = Union[StringToTranslate, Text]


def serialize(text: TransText):
    """
    Takes as input either a string to translate either an actual string and
    transforms it into a JSON-serializable structure that can be reconstructed
    using `unserialize()`.
    """

    if isinstance(text, str):
        return {
            'type': 'string',
            'value': text,
        }
    elif isinstance(text, StringToTranslate):
        return {
            'type': 'trans',
            'key': text.key,
            'count': text.count,
            'params': text.params,
        }
    else:
        raise ValueError('Cannot accept type "{}"'
                         .format(text.__class__.__name__))


def unserialize(wd: WordDictionary, text: Dict):
    """
    Transforms back a serialized value of `serialize()`
    """

    if not isinstance(text, Mapping):
        raise ValueError('Text has not the right format')

    try:
        t = text['type']

        if t == 'string':
            return text['value']
        elif t == 'trans':
            if not isinstance(text['params'], Mapping):
                raise ValueError('Params should be a dictionary')

            for param in text['params']:
                if not isinstance(param, str):
                    raise ValueError('Params are not all text-keys')

            return StringToTranslate(
                wd=wd,
                key=text['key'],
                count=text['count'],
                **text['params'],
            )
        else:
            raise ValueError('Unknown type "{}"'.format(t))
    except KeyError:
        raise ValueError('Not enough information to unserialize')


async def render(text: TransText, request: 'Request'):
    """
    Render either a normal string either a string to translate into an actual
    string for the specified request.
    """

    if isinstance(text, str):
        return text
    elif isinstance(text, StringToTranslate):
        return await text.render(request)
