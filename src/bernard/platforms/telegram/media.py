from typing import (
    Dict,
    List,
    Optional,
    Text,
)

from bernard.media.base import (
    BaseMedia,
)


class Photo(BaseMedia):
    """
    Abstract object over a Telegram photo object
    """

    def __init__(self, files: List[Dict]):
        self.files = files

    def __eq__(self, other):
        return all([
            self.__class__ == other.__class__,
            self.files == other.files,
        ])

    def __repr__(self):
        return f'Photo({repr(self.largest_id())})'

    def largest_id(self) -> Optional[Text]:
        # noinspection PyTypeChecker
        largest = max(self.files, key=lambda f: f['file_size'], default=None)
        return largest['file_id']
