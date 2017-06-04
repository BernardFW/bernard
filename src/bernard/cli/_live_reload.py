# coding: utf-8
"""
Live reload of code works the following way:

- There is a parent process that is just in charge of waiting for the child to
  die and then start it again, infinitely.
- The child process will start as usual and then look at its modules in order
  to watch them for changes. In case anything changes, then a small timeout
  is awaited then the process is exited with a special status code. When the
  parent picks this status code, it restarts the process.
"""
import asyncio
import aionotify
import logging
import sys
import subprocess
from os import path, environ
from bernard.conf import list_config_files, settings


logger = logging.getLogger('bernard.cli')


def _list_module_dirs():
    """
    List directory of modules
    """

    for m in sys.modules.values():
        try:
            yield from m.__path__
        except AttributeError:
            pass


def _list_config_dirs():
    """
    List directories holding config files
    """
    yield from (path.dirname(x) for x in list_config_files())


# noinspection PyUnresolvedReferences
def _list_syntax_error():
    """
    If we're going through a syntax error, add the directory of the error to
    the watchlist.
    """

    _, e, _ = sys.exc_info()
    if isinstance(e, SyntaxError) and hasattr(e, 'filename'):
        yield path.dirname(e.filename)


def list_dirs():
    """
    List all directories known to hold project code.
    """

    out = set()
    out.update(_list_config_dirs())
    out.update(_list_module_dirs())
    out.update(_list_syntax_error())
    return out


def exit_for_reload():
    """
    This triggers an exit with the appropriate signal for the parent to reload
    the code.
    """
    logger.warning('Reloading!')
    sys.exit(settings.CODE_RELOAD_EXIT)


async def start_child():
    """
    Start the child process that will look for changes in modules.
    """

    logger.info('Started to watch for code changes')

    loop = asyncio.get_event_loop()
    watcher = aionotify.Watcher()

    flags = (
        aionotify.Flags.MODIFY |
        aionotify.Flags.DELETE |
        aionotify.Flags.ATTRIB |
        aionotify.Flags.MOVED_TO |
        aionotify.Flags.MOVED_FROM |
        aionotify.Flags.CREATE |
        aionotify.Flags.DELETE_SELF |
        aionotify.Flags.MOVE_SELF
    )

    watched_dirs = list_dirs()

    for dir_name in watched_dirs:
        watcher.watch(path=dir_name, flags=flags)

    await watcher.setup(loop)

    while True:
        evt = await watcher.get_event()
        file_path = path.join(evt.alias, evt.name)

        if file_path in watched_dirs or file_path.endswith('.py'):
            await asyncio.sleep(settings.CODE_RELOAD_DEBOUNCE)
            break

    watcher.close()
    exit_for_reload()


def start_parent():
    """
    Start the parent that will simply run the child forever until stopped.
    """

    while True:
        args = [sys.executable] + sys.argv
        new_environ = environ.copy()
        new_environ["_IN_CHILD"] = 'yes'
        ret = subprocess.call(args, env=new_environ)

        if ret != settings.CODE_RELOAD_EXIT:
            return ret
