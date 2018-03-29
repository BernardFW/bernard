# coding: utf-8
import asyncio
import csv
import logging
import os.path
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Text,
    Tuple,
    Union,
)

import aionotify

from bernard.conf import (
    settings,
)

logger = logging.getLogger('bernard.i18n.loaders')


TransDict = Dict[Optional[Text], List[Tuple[Text, Text]]]
IntentDict = Dict[Optional[Text], Dict[Text, List[Tuple[Text, ...]]]]


class LiveFileLoaderMixin(object):
    """
    A mixin to help detecting live changes in translations and update them
    directly when saved.
    """

    THING = 'file'

    def __init__(self, *args, **kwargs):
        # noinspection PyArgumentList
        super(LiveFileLoaderMixin, self).__init__(*args, **kwargs)
        self._watcher = None
        self._file_path = None
        self._running = False
        self._locale = None
        self._kwargs = {}

    async def _load(self):
        """
        In this method you load the data from your file. You have to implement
        it. You can do whatever you want with it.
        """

        raise NotImplementedError

    async def _watch(self):
        """
        Start the watching loop.
        """

        file_name = os.path.basename(self._file_path)
        logger.info(
            'Watching %s "%s"',
            self.THING,
            self._file_path,
        )

        while self._running:
            evt = await self._watcher.get_event()

            if evt.name == file_name:
                await self._load()
                logger.info(
                    'Reloading changed %s from "%s"',
                    self.THING,
                    self._file_path
                )

    async def start(self, file_path, locale=None, kwargs=None):
        """
        Setup the watching utilities, start the loop and load data a first
        time.
        """

        self._file_path = os.path.realpath(file_path)
        self._locale = locale

        if kwargs:
            self._kwargs = kwargs

        if settings.I18N_LIVE_RELOAD:
            loop = asyncio.get_event_loop()

            self._running = True
            self._watcher = aionotify.Watcher()
            self._watcher.watch(
                path=os.path.dirname(self._file_path),
                flags=aionotify.Flags.MOVED_TO | aionotify.Flags.MODIFY,
            )
            await self._watcher.setup(loop)
            await self._load()

            loop.create_task(self._watch())
        else:
            await self._load()


class BaseTranslationLoader(object):
    """
    Base skeleton for a translations loader.

    Loaders must have an asynchronous `load` function that will be called with
    kwargs only. This function must load the translations and trigger an
    update event. It must NOT finish before the update is done.
    """

    def __init__(self):
        self.listeners = []  # type: List[Callable[[TransDict]], None]

    def on_update(self, cb: Callable[[TransDict], None]) -> None:
        """
        Registers an update listener

        :param cb: Callback that will get called on update
        """
        self.listeners.append(cb)

    def _update(self, data: TransDict, *args, **kwargs):
        """
        Propagate updates to listeners

        :param data: Data to propagate
        """

        for l in self.listeners:
            l(data, *args, **kwargs)

    async def load(self, **kwargs) -> None:
        """
        Starts the load cycle. Data must be loaded at least once before this
        function finishes.
        """

        raise NotImplementedError


class CsvTranslationLoader(LiveFileLoaderMixin, BaseTranslationLoader):
    """
    Loads data from a CSV file
    """

    THING = 'CSV translation'

    async def _load(self):
        """
        Load data from a Excel-formatted CSV file.
        """

        flags = self._kwargs.get('flags')

        if not flags:
            flags = {1: {}}

        cols = {k: [] for k in flags.keys()}

        with open(self._file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)

            for row in reader:
                for i, col in cols.items():
                    try:
                        val = row[i].strip()
                        assert val
                    except (IndexError, AssertionError):
                        pass
                    else:
                        col.append((row[0], val))

        for i, col in cols.items():
            self._update({self._locale: col}, flags[i])

    async def load(self, file_path, locale=None, flags=None):
        """
        Start the loading/watching process
        """

        await self.start(file_path, locale, {'flags': flags})


class BaseIntentsLoader(object):
    """
    Base skeleton for an intents loader.

    Loaders must have an asynchronous `load` function that will be called with
    kwargs only. This function must load the translations and trigger an
    update event. It must NOT finish before the update is done.
    """

    def __init__(self):
        self.listeners = []  # type: List[Callable[[IntentDict]], None]

    def on_update(self, cb: Callable[[IntentDict], None]) -> None:
        """
        Registers an update listener

        :param cb: Callback that will get called on update
        """
        self.listeners.append(cb)

    def _update(self, data: IntentDict):
        """
        Propagate updates to listeners

        :param data: Data to propagate
        """

        for l in self.listeners:
            l(data)

    async def load(self, **kwargs) -> None:
        """
        Starts the load cycle. Data must be loaded at least once before this
        function finishes.
        """

        raise NotImplementedError


ColRanges = List[Union[
    int,
    Tuple[int, Optional[int]],
]]


def extract_ranges(row, ranges: ColRanges) -> List[Text]:
    """
    Extracts a list of ranges from a row:

    - If the range is an int, just get the data at this index
    - If the range is a tuple of two ints, use them as indices in a slice
    - If the range is an int then a None, start the slice at the int and go
      up to the end of the row.
    """

    out = []

    for r in ranges:
        if isinstance(r, int):
            r = (r, r + 1)

        if r[1] is None:
            r = (r[0], len(row))

        out.extend(row[r[0]:r[1]])

    return [x for x in (y.strip() for y in out) if x]


class CsvIntentsLoader(LiveFileLoaderMixin, BaseIntentsLoader):
    """
    Load intents from a CSV
    """

    THING = 'CSV intents'

    async def _load(self):
        """
        Load data from a Excel-formatted CSV file.
        """

        key = self._kwargs['key']
        pos = self._kwargs['pos']
        neg = self._kwargs['neg']

        with open(self._file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = {}

            for row in reader:
                try:
                    data[row[key]] = data.get(row[key], []) + [
                        tuple(extract_ranges(row, [pos] + neg))
                    ]
                except IndexError:
                    pass

        self._update({self._locale: data})

    async def load(self,
                   file_path,
                   locale=None,
                   key: int = 0,
                   pos: int = 1,
                   neg: Optional[ColRanges] = None):
        """
        Start the loading/watching process
        """

        if neg is None:
            neg: ColRanges = [(2, None)]

        await self.start(file_path, locale, kwargs={
            'key': key,
            'pos': pos,
            'neg': neg,
        })
