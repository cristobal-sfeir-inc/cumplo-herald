"""Runtime constants and environment-variable bindings for cumplo-herald."""

import json
import os

from dotenv import load_dotenv

load_dotenv()


IS_TESTING = bool(os.getenv("IS_TESTING"))
LOG_FORMAT = "\n [%(levelname)s] %(message)s"
IFTTT_QUEUE = os.getenv("IFTTT_QUEUE", "ifttt")
WEBHOOK_QUEUE = os.getenv("WEBHOOK_QUEUE", "webhooks")


TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_SENDER_PHONE_NUMBER = os.getenv("TWILIO_SENDER_PHONE_NUMBER")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
TWILIO_CONTENT_SID = json.loads(os.getenv("TWILIO_CONTENT_SID", "{}"))
TWILIO_WEBHOOK_URL = os.getenv("TWILIO_WEBHOOK_URL")

NOTIFICATION_DELETION_MINUTES = int(os.getenv("NOTIFICATION_DELETION_MINUTES", "10000"))
