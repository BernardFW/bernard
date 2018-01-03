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

        ns = await self.expand_stacks(request, stacks)
        ns = self.split_stacks(ns)
        ns = self.clean_stacks(ns)

        await self.next(request, [Stack(x) for x in ns])

    async def expand_stacks(self, request: Request, stacks: List[Stack]):
        ns = []

        for stack in stacks:
            s = []

            for layer in stack.layers:
                async for sub_layer in self.expand(request, layer):
                    s.append(sub_layer)

            ns.append(s)

        return ns

    def split_stacks(self, stacks: List[List[BaseLayer]]) \
            -> List[List[BaseLayer]]:
        """
        First step of the stacks cleanup process. We consider that if inside
        a stack there's a text layer showing up then it's the beginning of a
        new stack and split upon that.
        """

        ns: List[List[BaseLayer]] = []

        for stack in stacks:
            cur: List[BaseLayer] = []

            for layer in stack:
                if cur and isinstance(layer, lyr.RawText):
                    ns.append(cur)
                    cur = []

                cur.append(layer)

            if cur:
                ns.append(cur)

        return ns

    def clean_stacks(self, stacks: List[List[BaseLayer]]) \
            -> List[List[BaseLayer]]:
        """
        Two cases: if a stack finishes by a sleep then let's keep it (it means
        that there was nothing after the text). However if the stack finishes
        with something else (like a quick reply) then we don't risk an
        is preserved.
        """

        ns: List[List[BaseLayer]] = []

        for stack in stacks:
            if isinstance(stack[-1], lyr.Sleep):
                ns.extend([x] for x in stack)
            else:
                ns.append([x for x in stack if not isinstance(x, lyr.Sleep)])

        last = ns[-1]
        if len(last) == 1 and isinstance(last[0], lyr.Sleep):
            return ns[:-1]
        else:
            return ns

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
