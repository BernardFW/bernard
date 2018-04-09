# coding: utf-8
from bernard import (
    layers as lyr,
)
from bernard.analytics import (
    page_view,
)
from bernard.engine import (
    BaseState,
)
from bernard.i18n import (
    translate as t,
)


class __project_name_camel__State(BaseState):
    """
    Root class for __project_name_readable__.

    Here you must implement "error" and "confused" to suit your needs. They
    are the default functions called when something goes wrong. The ERROR and
    CONFUSED texts are defined in `i18n/en/responses.csv`.
    """

    @page_view('/bot/error')
    async def error(self) -> None:
        """
        This happens when something goes wrong (it's the equivalent of the
        HTTP error 500).
        """

        self.send(lyr.Text(t.ERROR))

    @page_view('/bot/confused')
    async def confused(self) -> None:
        """
        This is called when the user sends a message that triggers no
        transitions.
        """

        self.send(lyr.Text(t.CONFUSED))

    async def handle(self) -> None:
        raise NotImplementedError


class Hello(__project_name_camel__State):
    """
    Example "Hello" state, to show you how it's done. You can remove it.

    Please note the @page_view decorator that allows to track the viewing of
    this page using the analytics provider set in the configuration. If there
    is no analytics provider, nothing special will happen and the handler
    will be called as usual.
    """

    @page_view('/bot/hello')
    async def handle(self):
        self.send(lyr.Text(t.HELLO))
