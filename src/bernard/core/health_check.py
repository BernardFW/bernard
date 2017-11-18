# coding: utf-8


class HealthCheckFail(object):
    """
    This object describes a failed health check.

    The code is a unique code describing the health check itself and must be
    unique for each check. This is in order to be able to write a documentation
    of them at some point.
    """

    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
