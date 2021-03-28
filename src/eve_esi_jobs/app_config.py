"""App config values

TODO support a more complex logger, with log to file
"""
import logging
import os

import click

APP_NAME = os.getenv("PFMSOFT_eve_esi_jobs_APP_NAME", "Pfmsoft-Eve-Esi")
"""The name of the app. Should be namespaced to prevent collision."""

logger = logging.getLogger(APP_NAME)

APP_DIR = os.getenv(
    "PFMSOFT_eve_esi_jobs_APP_DIR", click.get_app_dir(APP_NAME, force_posix=True)
)
"""The app data directory. Location is system dependent."""

SCHEMA_URL = os.getenv(
    "PFMSOFT_eve_esi_jobs_SCHEMA_URL", "https://esi.evetech.net/latest/swagger.json"
)
"""The url to the current version of the Eve ESI schema."""

LOG_LEVEL = os.getenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(logging.WARNING))
"""App wide setting for log level"""

# TESTING = os.getenv("PFMSOFT_eve_esi_jobs_TESTING", "False")
# """"""
