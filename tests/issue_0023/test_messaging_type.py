import pytest

from bernard.platforms.facebook.layers import MessageTag, MessagingType


def test_construct_check():
    with pytest.raises(ValueError):
        MessagingType(response=True, update=True)

    assert MessagingType(response=True)


def test_equality():
    mt1 = MessagingType(response=True)
    mt2 = MessagingType(response=True)
    mt3 = MessagingType(subscription=True)

    assert mt1 == mt2
    assert mt1 != mt3


def test_repr():
    mt = MessagingType(response=True)
    assert repr(mt) == "MessagingType('response')"

    mt = MessagingType(update=True)
    assert repr(mt) == "MessagingType('update')"

    mt = MessagingType(tag=MessageTag.ACCOUNT_UPDATE)
    assert repr(mt) == "MessagingType('tag=ACCOUNT_UPDATE')"

    mt = MessagingType(subscription=True)
    assert repr(mt) == "MessagingType('subscription')"


def test_serialize():
    mt = MessagingType(response=True)
    assert mt.serialize() == {"messaging_type": "RESPONSE"}

    mt = MessagingType(update=True)
    assert mt.serialize() == {"messaging_type": "UPDATE"}

    mt = MessagingType(tag=MessageTag.ACCOUNT_UPDATE)
    assert mt.serialize() == {
        "messaging_type": "MESSAGE_TAG",
        "tag": "ACCOUNT_UPDATE",
    }

    mt = MessagingType(subscription=True)
    assert mt.serialize() == {"messaging_type": "NON_PROMOTIONAL_SUBSCRIPTION"}
