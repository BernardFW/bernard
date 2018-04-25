from bernard import (
    layers as lyr,
)
from bernard.engine.triggers import (
    BaseTrigger,
)

from .store import (
    cs,
)


class Number(BaseTrigger):
    """
    This trigger will try to interpret what the user sends as a number. If it
    is a number, then it's compared to the number to guess in the context.
    The `is_right` parameter allows to say if you want the trigger to activate
    when the guess is right or not.
    """

    def __init__(self, request, is_right):
        super().__init__(request)
        self.is_right = is_right
        self.user_number = None

    # noinspection PyMethodOverriding
    @cs.inject()
    async def rank(self, context) -> float:
        number = context.get('number')

        if not number:
            return .0

        try:
            self.user_number = int(self.request.get_layer(lyr.RawText).text)
        except (KeyError, ValueError, TypeError):
            return .0

        is_right = number == self.user_number

        return 1. if is_right == self.is_right else .0
