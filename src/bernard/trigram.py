# coding: utf-8
"""
Trigram computation utils. Although the algorithm are pretty different, the
code here is inspired from PostgreSQL's pg_trgm module and should give similar
or identical results.
"""
import re
from collections import (
    deque,
)
from typing import (
    Iterable,
    List,
    Optional,
    Text,
    Tuple,
    TypeVar,
    Union,
)

from unidecode import (
    unidecode,
)

RE_WHITESPACES = re.compile(r'[\W.,;?!\'"«»\-_\s]+')

T = TypeVar('T')


def normalize(string: Text) -> Text:
    """
    Normalizes a string to encompass various things humans tend to get wrong:

    - Put everything lowercase
    - Drop accents
    - Transform all whitespaces sequences into a single space
    - Remove spaces before and after punctuation
    """

    string = string.lower()
    string = unidecode(string)
    string = RE_WHITESPACES.sub(' ', string).strip()

    return string


def make_words(string: Text) -> List[Text]:
    return string.split(' ')


def make_trigrams(i: Iterable[T]) \
        -> Iterable[Tuple[Optional[T], Optional[T], Optional[T]]]:
    """
    Compute all trigrams of an iterable and yield them. You probably want
    to do something like:

    >>> t = set(make_trigrams('hi there'))
    """
    q = deque([None, None, None])

    def nxt():
        q.append(x)
        q.popleft()
        return tuple(c if c is not None else ' ' for c in q)

    for x in i:
        yield nxt()

    if q[-1] is not None:
        x = None
        yield nxt()


class Trigram(object):
    """
    This represents a "compiled" trigram object. It is able to compute its
    similarity with other trigram objects.
    """

    def __init__(self, string):
        self._string = string
        self._norm = normalize(string)
        self._words = make_words(self._norm)
        self._trigrams = set(t for w in self._words for t in make_trigrams(w))

    def __repr__(self):
        return f'Trigram({repr(self._norm)})'

    def similarity(self, other: 'Trigram') -> float:
        """
        Compute the similarity with the provided other trigram.
        """
        if not len(self._trigrams) or not len(other._trigrams):
            return 0

        count = float(len(self._trigrams & other._trigrams))
        len1 = float(len(self._trigrams))
        len2 = float(len(other._trigrams))

        return count / (len1 + len2 - count)

    def __mod__(self, other: 'Trigram') -> float:
        """
        Shortcut notation using modulo symbol.
        """
        return self.similarity(other)


class Matcher(object):
    """
    Allows to match several trigrams at once. This is useful to detect intents.
    """

    def __init__(self, trigrams: List[Union[Trigram, Tuple[Trigram, ...]]]):
        self.trigrams = [
            (t,) if isinstance(t, Trigram) else t
            for t in trigrams
        ]

    def _match(self, local: Tuple[Trigram, ...], other: Trigram) -> float:
        """
        Match a trigram with another one. If the negative matching wins,
        returns an inverted matching.
        """

        pos = local[0] % other
        neg = max((x % other for x in local[1:]), default=0)

        if neg > pos:
            return 0.0

        return pos

    def similarity(self, other: Trigram) -> float:
        """
        Find the best similarity within known trigrams.
        """
        return max((self._match(x, other) for x in self.trigrams), default=0)

    def __mod__(self, other) -> float:
        """
        Shortcut notation using the modulo operator.
        """
        return self.similarity(other)


L = TypeVar('L')


class LabelMatcher(object):
    """
    Allows to match trigrams and associate an arbitrary label to them. When
    matching, the label will be returned along with the score.
    """

    def __init__(self, trigrams: List[Tuple[Trigram, L]]):
        self.trigrams = trigrams

    def similarity(self, other: Trigram) -> Tuple[float, L]:
        """
        Returns the best matching score and the associated label.
        """

        return max(
            ((t % other, l) for t, l in self.trigrams),
            key=lambda x: x[0],
        )
