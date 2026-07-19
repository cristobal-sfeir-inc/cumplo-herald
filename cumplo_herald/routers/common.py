"""Common router: event notification and notification-clearing endpoints."""

from copy import deepcopy
from http import HTTPStatus
from logging import getLogger
from typing import cast

import arrow
from cumplo_common.database import firestore
from cumplo_common.models import Notification, PublicEvent, User
from fastapi import APIRouter, HTTPException, Request

from cumplo_herald.adapters.channels import CHANNELS_BY_TYPE
from cumplo_herald.utils.constants import NOTIFICATION_DELETION_MINUTES

logger = getLogger(__name__)

router = APIRouter()


@router.post("/{event}/notify", status_code=HTTPStatus.NO_CONTENT)
async def notify_event(request: Request, event: PublicEvent, payload: dict) -> None:
    """
    Notifies the given event with the given payload through the user's channels.

    Raises:
        HTTPException: If the notification was already sent (status 208 ALREADY_REPORTED)

    """
    user = cast(User, request.state.user)
    content = event.model.model_validate(payload)

    if not user.should_notify(event, content):
        raise HTTPException(HTTPStatus.ALREADY_REPORTED)

    notification = Notification.new(event=event, content_id=content.id)
    user.notifications[notification.id] = notification
    firestore.client.users.update(user, "notifications")  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common

    for channel_configuration in user.channels.values():
        if not channel_configuration.enabled:
            logger.info(f"Channel {channel_configuration.id} is disabled")
            continue

        if not channel_configuration.event_enabled(event):
            logger.info(f"Channel {channel_configuration.id} is not enabled for event {event}")
            continue

        channel = CHANNELS_BY_TYPE[channel_configuration.type_](user, channel_configuration)
        channel.notify(event, content)


@router.post("/notifications/clear", status_code=HTTPStatus.NO_CONTENT)
async def clear_notifications() -> None:
    """Delete all expired notifications for all users."""
    for user in firestore.client.users.list():  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common
        logger.info(f"Clearing expired notifications for user {user.name}")
        for key, notification in deepcopy(user.notifications).items():
            if arrow.get(notification.date).shift(minutes=NOTIFICATION_DELETION_MINUTES) < arrow.utcnow():
                logger.info(f"Deleting expired notification {key} for user {user.name}")
                del user.notifications[key]

        firestore.client.users.update(user, "notifications")  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common
