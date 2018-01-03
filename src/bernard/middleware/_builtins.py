class BaseMiddleware(object):
    """
    Base class for middlewares. It's just useful to get the `self.next`
    automatically.
    """

    def __init__(self, next_):
        self.next = next_
