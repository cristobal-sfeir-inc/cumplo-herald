"""Private WhatsApp router: demo endpoint to trigger WhatsApp notifications directly."""

import json
from http import HTTPStatus
from logging import getLogger
from typing import cast

import ulid
from cumplo_common.database import firestore
from cumplo_common.models import Notification, PublicEvent, User, WhatsappConfiguration
from fastapi import APIRouter, HTTPException, Request

from cumplo_herald.adapters.channels.whatsapp import Whatsapp

logger = getLogger(__name__)

router = APIRouter(prefix="/whatsapp")


# NOTE: This endpoint is used for demo purposes only.
@router.post("/{event}/notify", status_code=HTTPStatus.CREATED)
async def notify_whatsapp_event(request: Request, event: PublicEvent, payload: dict) -> None:
    """
    Notifies the given event with the given payload through the user's channels.

    Raises:
        HTTPException: If the phone number is not provided (status 400 BAD_REQUEST)

    """
    user = cast(User, request.state.user)
    if not (phone_number := payload.get("phone_number")):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Phone number is required")

    if not (content := payload.get("content")):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Content is required")

    try:
        content = event.model.model_validate(json.loads(content))
    except Exception:
        logger.exception("Error parsing content")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    phone_number = phone_number.replace(" ", "")
    configuration = WhatsappConfiguration(
        id=ulid.new(),
        enabled=True,
        enabled_events={event},
        phone_number=phone_number,
    )
    channel = Whatsapp(user, configuration)
    channel.notify(event, content)

    logger.info(f"Sending WhatsApp notification to {phone_number} for event {event}")
    notification = Notification.new(event=event, content_id=content.id)
    user.notifications[notification.id] = notification
    firestore.client.users.update(user, "notifications")  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common
