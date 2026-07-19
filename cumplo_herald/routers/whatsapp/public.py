"""Public WhatsApp router: Twilio webhook handler for button-reply interactions."""

from enum import StrEnum
from http import HTTPStatus
from logging import getLogger

from cumplo_common.database import firestore
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from cumplo_herald.utils.constants import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_SENDER_PHONE_NUMBER,
    TWILIO_WEBHOOK_URL,
)

logger = getLogger(__name__)

router = APIRouter(prefix="/whatsapp")


class TwilioMessageType(StrEnum):
    """Twilio message types."""

    BUTTON = "button"


class TwilioQuickReply(StrEnum):
    """Twilio quick reply types."""

    DISMISS = "dismiss"


async def validate_twilio_request(request: Request) -> bool:
    """Validate that the request actually came from Twilio."""
    form_data = await request.form()
    signature = request.headers.get("x-twilio-signature", "")
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    return validator.validate(TWILIO_WEBHOOK_URL, dict(form_data), signature)


@router.post("/messages")
async def whatsapp_webhook(
    sender: str | None = Form(None, alias="From"),
    text: str | None = Form(None, alias="ButtonText"),
    payload: str | None = Form(None, alias="ButtonPayload"),
    message_type: str | None = Form(None, alias="MessageType"),
    valid: bool = Depends(validate_twilio_request),  # noqa: FBT001
) -> None:
    """
    Handle WhatsApp webhook requests for button responses.

    Raises:
        HTTPException: If the request is invalid.

    """
    if not valid:
        logger.warning("Invalid Twilio signature")
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)

    if not payload or not text or message_type != TwilioMessageType.BUTTON:
        logger.warning("Twilio webhook is missing required fields")
        return

    id_user, id_notification = payload.split(":")

    if not (user := firestore.client.users.get(id_user)):  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common
        logger.error(f"User {id_user} not found")
        return

    if not (notification := user.notifications.get(id_notification)):
        logger.error(f"Notification {id_notification} not found for user {id_user}")
        return

    response = None
    match text.casefold():
        case TwilioQuickReply.DISMISS:
            if notification.dismissed:
                logger.info(f"Notification {id_notification} already dismissed")
                return
            notification.dismissed = True
            user.notifications[id_notification] = notification
            firestore.client.users.update(user, "notifications")  # pyright: ignore[reportPrivateImportUsage]  # TODO(NOT-26): export client in cumplo-common
            response = f"*Funding Request N° {notification.content_id}*\n🔕 *Dismissed*"
        case _:
            logger.warning(f"Unknown button text: {text}")

    if not sender or not sender.startswith("whatsapp:"):
        logger.error("No sender phone number provided in WhatsApp webhook")
        return

    if response:
        logger.info(f"Replying '{text}' message to {sender}")
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(to=sender, from_=f"whatsapp:{TWILIO_SENDER_PHONE_NUMBER}", body=response)
