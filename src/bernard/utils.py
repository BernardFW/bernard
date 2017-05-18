# coding: utf-8
import importlib
import asyncio
from typing import Text, Coroutine, Any


def import_class(name: Text) -> object:
    """
    Import a class based on its full name.

    :param name: name of the class
    """

    parts = name.split('.')
    module_name = parts[:-1]
    class_name = parts[-1]
    module_ = importlib.import_module('.'.join(module_name))
    return getattr(module_, class_name)


def run(task: Coroutine) -> Any:
    """
    Run a task in the default asyncio look.

    :param task: Task to run
    """

    return asyncio.get_event_loop().run_until_complete(task)
