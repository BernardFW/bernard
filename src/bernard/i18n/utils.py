import re
from typing import Dict, Text, List, Optional, Tuple
from collections import OrderedDict


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


class LocalesDict(object):
    def __init__(self):
        self.dict = OrderedDict()
        self._choice_cache = {}

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


class LocalesFlatDict(LocalesDict):
    """
    That used to be in LocalesDict but the children diverged and now this
    method is alone. It could have gone directly into the intents loader but
    it feels like it'll have to go outside again, so for now it stays in this
    class.
    """

    def update(self, new_data: Dict[Text, Dict[Text, Text]]):
        """
        Receive an update from a loader.

        :param new_data: New translation data from the loader
        """

        for locale, data in new_data.items():
            if locale not in self.dict:
                self.dict[locale] = {}

            self.dict[locale].update(data)
