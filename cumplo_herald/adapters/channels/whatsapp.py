"""WhatsApp channel adapter for sending notifications via the Twilio API."""

from decimal import Decimal
from logging import getLogger
from typing import Any, override

from cumplo_common.models import ChannelType, FundingRequest, Notification, PublicEvent, User, WhatsappConfiguration
from pydantic import Field
from twilio.rest import Client

from cumplo_herald.ports.channel import Channel, Message
from cumplo_herald.utils.constants import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_CONTENT_SID,
    TWILIO_MESSAGING_SERVICE_SID,
    TWILIO_SENDER_PHONE_NUMBER,
)

logger = getLogger(__name__)


class Whatsapp(Channel):
    """Channel adapter that delivers messages to a user's WhatsApp number via Twilio."""

    configuration: WhatsappConfiguration  # pyright: ignore[reportIncompatibleVariableOverride]  # TODO(NOT-26): fix via Channel generics
    type_ = ChannelType.WHATSAPP
    client: Client
    user: User

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    @override
    def send(self, event: PublicEvent, message: Message) -> None:
        """Send the message to the user."""
        logger.info(f"Sending message: {message.model_dump_json()}")
        self.client.messages.create(
            content_sid=TWILIO_CONTENT_SID[event],
            from_=f"whatsapp:{TWILIO_SENDER_PHONE_NUMBER}",
            to=f"whatsapp:{self.configuration.phone_number}",
            content_variables=message.model_dump_json(),
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
        )

    @override
    def _write_funding_request_promising(self, content: FundingRequest) -> Message:
        """Write the message for the funding_request.promising event."""

        class WhatsappMessage(Message):
            score: Decimal = Field(ge=0, le=1)
            borrower: str = Field(min_length=1)
            duration: str = Field(min_length=1)
            credit_type: str = Field(min_length=1)
            funding_request_id: str = Field(min_length=1)
            monthly_profit_rate: Decimal = Field(ge=0, le=100)
            installments: str = Field(...)
            user_id: str = Field(min_length=1)
            notification_id: str = Field(min_length=1)

        monthly_profit_rate = round(Decimal(content.monthly_profit_rate * 100), ndigits=2)

        borrower = content.borrower.name if content.borrower else None
        borrower = borrower or (content.debtors[0].name if content.debtors else None)
        borrower = borrower or "unknown"

        return WhatsappMessage(
            score=content.score,
            borrower=borrower.title(),
            duration=str(content.duration),
            credit_type=content.credit_type.title(),
            funding_request_id=str(content.id),
            monthly_profit_rate=monthly_profit_rate,
            installments=str(content.installments),
            notification_id=Notification.build_id(PublicEvent.FUNDING_REQUEST_PROMISING, content.id),
            user_id=str(self.user.id),
        )
