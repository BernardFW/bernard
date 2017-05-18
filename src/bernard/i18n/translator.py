# coding: utf-8
from typing import List, Text, Optional, Dict
from bernard.conf import settings
from bernard.utils import import_class, run
from .loaders import BaseTranslationLoader


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


class WordDictionary(object):
    """
    That's where the actual translation happens. It stores all translations in
    memory, puts the parameters in place and so on.
    """

    def __init__(self):
        self.dict = {}
        self.loaders = []  # type: List[BaseTranslationLoader]
        self._init_loaders()

    def _init_loaders(self) -> None:
        """
        This creates the loaders instances and subscribes to their updates.
        """

        for loader in settings.I18N_TRANSLATION_LOADERS:
            loader_class = import_class(loader['loader'])
            instance = loader_class()
            instance.on_update(self.update)
            run(instance.load(**loader['params']))

    def update(self, new_data: Dict[Text, Text]):
        """
        Receive an update from a loader.

        :param new_data: New translation data from the loader
        """

        self.dict.update(new_data)

    def get(self, key: Text, count: Optional[int]=None, **params) -> Text:
        """
        Get the appropriate translation given the specified parameters.

        :param key: Translation key
        :param count: Count for plurals
        :param params: Params to be substituted
        """

        if count is not None:
            raise TranslationError('Count parameter is not supported yet')

        try:
            out = self.dict[key]
        except KeyError:
            raise MissingTranslationError('Translation "{}" does not exist'
                                          .format(key))

        try:
            out = out.format(**params)
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

    def render(self, request=None):
        """
        Render the translation for the specified request. If no request is
        specified, do as good as possible.

        :param request: Bot request. No one knows what it's going to look like
                        so far.
        """

        return self.LINE_SEPARATOR.join(self.render_list(request))

    # noinspection PyUnusedLocal
    def render_list(self, request=None) -> List[Text]:
        """
        Render the translation as a list if there is multiple strings for this
        single key.

        :param request: Bot request.
        """

        return [self.wd.get(self.key, self.count, **self.params)]


class Translator(object):
    """
    That's the basic object that you use to produce translations.
    """

    def __init__(self, wd: WordDictionary):
        """
        We need the word dictionary here in order to pass it to the string to
        translate when it will get rendered.

        :param wd: a configured WordDictionary
        """
        self.wd = wd

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
