"""FastAPI application entry point: configures logging, middleware, and routers."""

import warnings
from logging import DEBUG, ERROR, INFO, basicConfig, getLogger

import google.cloud.logging
from cumplo_common.dependencies import authenticate, is_admin
from cumplo_common.middlewares import PubSubMiddleware
from fastapi import Depends, FastAPI

from cumplo_herald.routers import common, whatsapp
from cumplo_herald.utils.constants import IS_TESTING, LOG_FORMAT

getLogger("cumplo_common").setLevel(DEBUG)


if IS_TESTING:
    basicConfig(level=INFO, format=LOG_FORMAT)
else:
    client = google.cloud.logging.Client()
    client.setup_logging(log_level=DEBUG)

# NOTE: Mute noisy third-party loggers
for module in ("google", "urllib3", "werkzeug", "twilio", "multipart"):
    getLogger(module).setLevel(ERROR)

warnings.filterwarnings("ignore", module="pydantic")

app = FastAPI()
app.add_middleware(PubSubMiddleware)

app.include_router(common.router, dependencies=[Depends(authenticate)])
app.include_router(whatsapp.public.router)

# NOTE: This router is used for demo purposes only.
app.include_router(whatsapp.private.router, dependencies=[Depends(authenticate), Depends(is_admin)])
