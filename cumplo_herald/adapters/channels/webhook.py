"""Webhook channel adapter for forwarding events to arbitrary HTTP endpoints."""

from typing import override

from cumplo_common.integrations.cloud_tasks import CloudTasks
from cumplo_common.models import ChannelType, FundingRequest, PublicEvent, WebhookConfiguration

from cumplo_herald.ports.channel import Channel, Message
from cumplo_herald.utils.constants import WEBHOOK_QUEUE


class WebhookMessage(Message):
    """Pydantic message payload for webhook deliveries."""

    event: PublicEvent
    data: dict


class Webhook(Channel):
    """Channel adapter that posts event payloads to a user-configured HTTP endpoint."""

    configuration: WebhookConfiguration  # pyright: ignore[reportIncompatibleVariableOverride]  # TODO(NOT-26): fix via Channel generics
    type_ = ChannelType.WEBHOOK

    @override
    def send(self, event: PublicEvent, message: Message) -> None:
        """Send the message to the user."""
        CloudTasks.create_task(
            url=self.configuration.url,
            queue=WEBHOOK_QUEUE,
            payload=message.model_dump(),
            task_id="WEBHOOK-WEBHOOK",
            is_internal=False,
        )

    @staticmethod
    @override
    def _write_funding_request_promising(content: FundingRequest) -> WebhookMessage:  # pyright: ignore[reportIncompatibleMethodOverride]  # TODO(NOT-26): fix via Channel generics
        """Write the message for the funding_request.promising event."""
        return WebhookMessage(event=PublicEvent.FUNDING_REQUEST_PROMISING, data=content.json())
