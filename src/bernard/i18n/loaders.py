# coding: utf-8
import csv
from typing import Callable, Dict, Text, List


class BaseLoader(object):
    """
    Base skeleton for a loader.

    Loaders must have an asynchronous `load` function that will be called with
    kwargs only. This function must load the translations and trigger an
    update event. It must NOT finish before the update is done.
    """

    def __init__(self):
        self.listeners = []  # type: List[Callable[[Dict[Text, Text]]], None]

    def on_update(self, cb: Callable[[Dict[Text, Text]], None]) -> None:
        """
        Registers an update listener

        :param cb: Callback that will get called on update
        """
        self.listeners.append(cb)

    def _update(self, data: Dict[Text, Text]):
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


class CsvLoader(BaseLoader):
    """
    Loads data from a CSV file
    """

    async def load(self, file_path: Text):
        """
        Load data from a Excel-formatted CSV file.

        :param file_path: path to the file to read 
        """

        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            data = {k: v for k, v in reader}
        self._update(data)
