import re
from typing import List, Text as TextT
from bernard import layers as lyr
from bernard.conf import settings
from bernard.engine.request import Request
from bernard.i18n import render
from bernard.layers import Stack, BaseLayer


class BaseMiddleware(object):
    """
    Base class for middlewares. It's just useful to get the `self.next`
    automatically.
    """

    def __init__(self, next_):
        self.next = next_


class AutoSleep(BaseMiddleware):
    """
    Automatically add sleep between text messages so the user has some time to
    to read.
    """

    async def flush(self, request: Request, stacks: List[Stack]):
        """
        For all stacks to be sent, append a pause after each text layer.
        """

        ns = []

        for stack in stacks:
            s = []

            for layer in stack.layers:
                async for sub_layer in self.expand(request, layer):
                    s.append(sub_layer)

            ns.append(Stack(s))

        await self.next(request, ns)

    async def expand(self, request: Request, layer: BaseLayer):
        """
        Expand a layer into a list of layers including the pauses.
        """

        if isinstance(layer, lyr.RawText):
            t = self.reading_time(layer.text)
            yield layer
            yield lyr.Sleep(t)

        elif isinstance(layer, lyr.MultiText):
            texts = await render(layer.text, request, True)

            for text in texts:
                t = self.reading_time(text)
                yield lyr.RawText(text)
                yield lyr.Sleep(t)

        elif isinstance(layer, lyr.Text):
            text = await render(layer.text, request)
            t = self.reading_time(text)
            yield lyr.RawText(text)
            yield lyr.Sleep(t)

        else:
            yield layer

    def reading_time(self, text: TextT):
        """
        Computes the time in seconds that the user will need to read a bubble
        containing the text passed as parameter.
        """

        wc = re.findall(r'\w+', text)
        period = 60.0 / settings.USERS_READING_SPEED
        return float(len(wc)) * period + settings.USERS_READING_BUBBLE_START
