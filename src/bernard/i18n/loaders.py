# coding: utf-8
import csv
import aionotify
import asyncio
import logging
import os.path
from bernard.conf import settings
from typing import Callable, Dict, Text, List


logger = logging.getLogger('bernard.i18n.loaders')


TransDict = Dict[Text, Text]
IntentDict = Dict[Text, List[Text]]


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

    async def start(self, file_path):
        """
        Setup the watching utilities, start the loop and load data a first
        time.
        """

        self._file_path = os.path.realpath(file_path)

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

    def _update(self, data: TransDict):
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


class CsvTranslationLoader(LiveFileLoaderMixin, BaseTranslationLoader):
    """
    Loads data from a CSV file
    """

    THING = 'CSV translation'

    async def _load(self):
        """
        Load data from a Excel-formatted CSV file.
        """

        with open(self._file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = {k: v for k, v in reader}
        self._update(data)

    async def load(self, file_path):
        """
        Start the loading/watching process
        """

        await self.start(file_path)


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


class CsvIntentsLoader(LiveFileLoaderMixin, BaseIntentsLoader):
    """
    Load intents from a CSV
    """

    THING = 'CSV intents'

    async def _load(self):
        """
        Load data from a Excel-formatted CSV file.
        """

        with open(self._file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = {}

            for k, v in reader:
                data[k] = data.get(k, []) + [v]

        self._update(data)

    async def load(self, file_path):
        """
        Start the loading/watching process
        """

        await self.start(file_path)
