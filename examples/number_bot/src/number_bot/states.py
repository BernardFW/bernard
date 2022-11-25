from random import SystemRandom

from bernard import layers as lyr
from bernard.analytics import page_view
from bernard.engine import BaseState
from bernard.i18n import intents as its
from bernard.i18n import translate as t
from bernard.platforms.facebook import layers as fbl

from .store import cs

random = SystemRandom()


class NumberBotState(BaseState):
    """
    Root class for Number Bot.
    """

    @page_view("/bot/error")
    async def error(self) -> None:
        """
        This happens when something goes wrong (it's the equivalent of the
        HTTP error 500).
        """

        self.send(lyr.Text(t.ERROR))

    @page_view("/bot/confused")
    async def confused(self) -> None:
        """
        This is called when the user sends a message that triggers no
        transitions.
        """

        self.send(lyr.Text(t.CONFUSED))

    async def handle(self) -> None:
        raise NotImplementedError


class S001xWelcome(NumberBotState):
    """
    Welcome the user
    """

    @page_view("/bot/welcome")
    async def handle(self) -> None:
        name = await self.request.user.get_friendly_name()

        self.send(
            lyr.Text(t("WELCOME", name=name)),
            fbl.QuickRepliesList(
                [
                    fbl.QuickRepliesList.TextOption(
                        slug="play",
                        text=t.LETS_PLAY,
                        intent=its.LETS_PLAY,
                    ),
                ]
            ),
        )


class S002xGuessANumber(NumberBotState):
    """
    Define the number to guess behind the scenes and tell the user to guess it.
    """

    # noinspection PyMethodOverriding
    @page_view("/bot/guess-a-number")
    @cs.inject()
    async def handle(self, context) -> None:
        context["number"] = random.randint(1, 100)
        self.send(lyr.Text(t.GUESS_A_NUMBER))


class S003xGuessAgain(NumberBotState):
    """
    If the user gave a number that is wrong, we give an indication whether that
    guess is too low or too high.
    """

    # noinspection PyMethodOverriding
    @page_view("/bot/guess-again")
    @cs.inject()
    async def handle(self, context) -> None:
        user_number = self.trigger.user_number

        self.send(lyr.Text(t.WRONG))

        if user_number < context["number"]:
            self.send(lyr.Text(t.HIGHER))
        else:
            self.send(lyr.Text(t.LOWER))


class S004xCongrats(NumberBotState):
    """
    Congratulate the user for finding the number and propose to find another
    one.
    """

    @page_view("/bot/congrats")
    async def handle(self) -> None:
        self.send(
            lyr.Text(t.CONGRATULATIONS),
            fbl.QuickRepliesList(
                [
                    fbl.QuickRepliesList.TextOption(
                        slug="again",
                        text=t.PLAY_AGAIN,
                        intent=its.PLAY_AGAIN,
                    ),
                ]
            ),
        )
