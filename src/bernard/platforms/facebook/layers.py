from enum import Enum
from typing import Optional

from bernard.layers import BaseLayer


class MessageTag(Enum):
    """
    See https://developers.facebook.com/docs/messenger-platform
        /send-messages/message-tags
    """

    PAIRING_UPDATE = 'PAIRING_UPDATE'
    APPLICATION_UPDATE = 'APPLICATION_UPDATE'
    ACCOUNT_UPDATE = 'ACCOUNT_UPDATE'
    PAYMENT_UPDATE = 'PAYMENT_UPDATE'
    PERSONAL_FINANCE_UPDATE = 'PERSONAL_FINANCE_UPDATE'
    SHIPPING_UPDATE = 'SHIPPING_UPDATE'
    RESERVATION_UPDATE = 'RESERVATION_UPDATE'
    ISSUE_RESOLUTION = 'ISSUE_RESOLUTION'
    APPOINTMENT_UPDATE = 'APPOINTMENT_UPDATE'
    GAME_EVENT = 'GAME_EVENT'
    TRANSPORTATION_UPDATE = 'TRANSPORTATION_UPDATE'
    FEATURE_FUNCTIONALITY_UPDATE = 'FEATURE_FUNCTIONALITY_UPDATE'
    TICKET_UPDATE = 'TICKET_UPDATE'


class MessagingType(BaseLayer):
    """
    Allows to flag a message to indicate its "motive".

    See https://developers.facebook.com/docs/messenger-platform
        /send-messages#messaging_types
    """

    def __init__(self,
                 response: Optional[bool] = None,
                 update: Optional[bool] = None,
                 tag: Optional[MessageTag] = None,
                 subscription: Optional[bool] = None) -> None:
        self.response = response
        self.update = update
        self.tag = tag
        self.subscription = subscription

        self._args = [
            response,
            update,
            tag,
            subscription,
        ]

        if self._args.count(None) != 3:
            raise ValueError('You need to specify exactly one argument when '
                             'creating a MessagingType() layer.')

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.response == other.response \
               and self.update == other.update \
               and self.subscription == other.subscription

    def _repr_arguments(self):
        if self.response is not None:
            return ['response']

        if self.update is not None:
            return ['update']

        if self.tag is not None:
            return [f'tag={self.tag.value}']

        if self.subscription is not None:
            return ['subscription']

    def serialize(self):
        """
        Generates the messaging-type-related part of the message dictionary.
        """

        if self.response is not None:
            return {'messaging_type': 'RESPONSE'}

        if self.update is not None:
            return {'messaging_type': 'UPDATE'}

        if self.tag is not None:
            return {
                'messaging_type': 'MESSAGE_TAG',
                'tag': self.tag.value,
            }

        if self.subscription is not None:
            return {'messaging_type': 'NON_PROMOTIONAL_SUBSCRIPTION'}
