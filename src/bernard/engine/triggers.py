# coding: utf-8
from typing import Optional, Text as TextT, Callable, Type
from bernard.i18n.intents import Intent
from bernard.i18n import intents, render
from bernard.trigram import Matcher, Trigram
from bernard.engine.request import Request
from bernard import layers as l


class BaseTrigger(object):
    def __init__(self, request: Request):
        self.request = request

    @classmethod
    def builder(cls, *args, **kwargs) -> Callable[[Request], 'BaseTrigger']:
        def factory(request: Request):
            return cls(request, *args, **kwargs)
        factory.trigger_name = cls.__name__
        return factory

    def rank(self) -> Optional[float]:
        """
        Given the current request, ranks on a scale from 0 to 1 how likely it 
        is that this trigger matches it.
        """
        raise NotImplementedError

    def patch(self) -> None:
        """
        This method will be called when the trigger is selected. If you need
        to alter the request or the user context, this is where you need to do
        it.
        """
        pass


class Anything(BaseTrigger):
    """
    A trigger that will always match
    """

    def rank(self):
        """
        Always return 1
        """
        return 1.0


class Text(BaseTrigger):
    """
    A trigger that will match an intent in a text message
    """

    def __init__(self, request: Request, intent: Intent):
        super(Text, self).__init__(request)
        self.intent = intent

    async def rank(self) -> Optional[float]:
        """
        If there is a text layer inside the request, try to find a matching
        text in the specified intent.
        """

        if not self.request.has_layer(l.RawText):
            return

        tl = self.request.get_layer(l.RawText)
        matcher = Matcher([
            Trigram(x) for x in self.intent.strings(self.request)
        ])

        return matcher % Trigram(tl.text)


class Choice(BaseTrigger):
    """
    Triggers when the user does a choice.

    Choices are read from the transitions register.

    This trigger has two attributes: `slug` is the slug of choice made and
    `chosen` is the meta-info about this choice (text and intent).

    The optional `when` argument allows to limit matching to a single choice.
    """

    def __init__(self, request: Request, when: Optional[TextT]=None):
        super(Choice, self).__init__(request)
        self.when = when
        self.slug = None
        self.chosen = None

    # noinspection PyUnresolvedReferences
    def _rank_qr(self, choices):
        """
        Look for the QuickReply layer's slug into available choices.
        """

        try:
            qr = self.request.get_layer(l.QuickReply)
            self.chosen = choices[qr.slug]
            self.slug = qr.slug

            if self.when is None or self.when == qr.slug:
                return 1.0
        except KeyError:
            pass

    async def _rank_text(self, choices):
        """
        Try to match the TextLayer with choice's intents.
        """

        tl = self.request.get_layer(l.RawText)
        best = 0.0

        for slug, params in choices.items():
            strings = []

            if params['intent']:
                intent = getattr(intents, params['intent'])
                strings += intent.strings(self.request)

            if params['text']:
                strings.append(params['text'])

            matcher = Matcher([Trigram(x) for x in strings])
            score = matcher % Trigram(await render(tl.text, self.request))

            if score > best:
                self.chosen = params
                self.slug = slug
                best = score

        if self.when is None or self.slug == self.when:
            return best

    # noinspection PyUnresolvedReferences
    async def rank(self):
        """
        Try to find a choice in what the user did:

        - If there is a quick reply, then use its payload as choice slug
        - Otherwise, try to match each choice with its intent
        """

        choices = self.request.get_trans_reg('choices')

        if not choices:
            return

        if self.request.has_layer(l.QuickReply):
            return self._rank_qr(choices)
        elif self.request.has_layer(l.RawText):
            return await self._rank_text(choices)


class Action(BaseTrigger):
    """
    Triggered by "actions". An action is a postback message with a "action"
    field in its payload. This trigger simply matches actions on text.
    """

    def __init__(self, request: Request, action: TextT):
        super(Action, self).__init__(request)
        self.action = action

    # noinspection PyUnresolvedReferences
    def rank(self) -> Optional[float]:
        if self.request.has_layer(l.Postback):
            pb = self.request.get_layer(l.Postback)

            try:
                if pb.payload['action'] == self.action:
                    return 1.0
            except (TypeError, KeyError):
                pass


class Layer(BaseTrigger):
    """
    Gets triggered when the message contains a specific layer
    """

    def __init__(self, request: Request, layer_type: Type[l.BaseLayer]):
        super(Layer, self).__init__(request)
        self.layer_type = layer_type

    def rank(self) -> Optional[float]:
        """
        Simply test the presence of layer type
        """

        return 1.0 if self.request.has_layer(self.layer_type) else 0.0


class BaseSlugTrigger(BaseTrigger):
    """
    Common type for slug-based classes that would have exactly the same code
    otherwise.
    """

    LAYER_TYPE = None

    def __init__(self, request: Request, slug: Optional[Text]=None):
        super(BaseSlugTrigger, self).__init__(request)
        self.slug = slug

    def rank(self) -> Optional[float]:
        if self.request.has_layer(self.LAYER_TYPE):
            if self.request.get_layer(self.LAYER_TYPE).slug == self.slug or \
                    self.slug is None:
                return 1.0


class LinkClick(BaseSlugTrigger):
    """
    This layer is triggered by the user clicking on an URL button.
    """

    LAYER_TYPE = l.LinkClick


class CloseWebview(BaseSlugTrigger):
    """
    This layer is triggered by the user closing a webview.
    """

    LAYER_TYPE = l.CloseWebview
