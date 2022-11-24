#!/usr/bin/env python3

from os import environ, path
from sys import path as py_path
from sys import stderr

ROOT = path.dirname(__file__)

environ.setdefault(
    "BERNARD_SETTINGS_FILE",
    path.join(ROOT, "src/number_bot/settings.py"),
)


if __name__ == "__main__":
    try:
        py_path.append(path.join(ROOT, "src"))
        from bernard.misc.main import main

        main()
    except ImportError:
        print(
            "Could not import BERNARD. Is your environment correctly " "configured?",
            file=stderr,
        )
        exit(1)
