# coding: utf-8


class Responder(object):
    def clear(self):
        raise NotImplementedError

    def flush(self):
        raise NotImplementedError
