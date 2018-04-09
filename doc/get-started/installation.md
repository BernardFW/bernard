Installation
============

BERNARD is a standard Python package and has a few dependencies. We'll
try to give pointers at how to work with it.

## Requirements

Overall, BERNARD requires:

- **Python 3.6+** as it uses heavily very recent syntaxes and features
- **Redis** for short-term memory

## Python setup

While this is not a tutorial on how to use Python, we'll try to give you
a few links to help you getting started.

In order to have a development environment that is easy to manage, it is
recommended to have a virtual environment. You can have a look over
there for guidance:

- Linux/OSX: you can use [pyenv](https://github.com/pyenv/pyenv-installer)
- Windows: you can follow
  [this tutorial](http://timmyreilly.azurewebsites.net/python-pip-virtualenv-installation-on-windows/)
  and then
  [this one](http://timmyreilly.azurewebsites.net/setup-a-virtualenv-for-python-3-on-windows/)

In order to write code, the author recommends to use
[PyCharm Community](https://www.jetbrains.com/pycharm/download/#section=linux),
which is a really powerful editor. In any case, you should configure
your IDE to use the virtualenv you created.

## Install BERNARD

Finally, when your environment is set, you can install Bernard. You can
simply do this with Pip:

```console
$ pip install bernard
```

## Redis setup

No particular Redis configuration is required. You can install it from
your package manager of follow the instructions found in the
[redis quickstart](https://redis.io/topics/quickstart).

## Wrap-up

You need to get your hands on a Python 3.6+ environment and a Redis
server. That's a wide subject to cover, so we'll leave you to it!

**Next step**: [start](./start.md)
