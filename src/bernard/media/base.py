# coding: utf-8


class BaseMedia(object):
    """
    Different platforms have different ways of representing medias. The goal
    of this object is to provide a way to know which platform the media came
    from and a way to convert it into a media that can be sent to another
    platform.
    """

    def __eq__(self, other):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError


class UrlMedia(BaseMedia):
    """
    That is a very simple media that represents something accessible over an
    URL.
    """

    def __init__(self, url):
        self.url = url

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.url == other.url)

    def __repr__(self):
        return 'UrlMedia({})'.format(repr(self.url))
