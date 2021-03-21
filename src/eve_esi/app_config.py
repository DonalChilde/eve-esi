"""App config values"""
import logging
import os

import click

APP_NAME = os.getenv("PFMSOFT_EVE_ESI_APP_NAME", "Eve-Esi")
logger = logging.getLogger(APP_NAME)
APP_DIR = os.getenv(
    "PFMSOFT_EVE_ESI_APP_DIR", click.get_app_dir(APP_NAME, force_posix=True)
)
SCHEMA_URL = os.getenv(
    "PFMSOFT_EVE_ESI_SCHEMA_URL", "https://esi.evetech.net/latest/swagger.json"
)
LOG_LEVEL = os.getenv("PFMSOFT_EVE_ESI_LOG_LEVEL", str(logging.WARNING))
TESTING = os.getenv("PFMSOFT_EVE_ESI_TESTING", "False")
