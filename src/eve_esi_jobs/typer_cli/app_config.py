"""App config values
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

import click


class EveEsiJobConfig:
    def __init__(
        self, app_name: str, app_dir: str, schema_url: str, log_level: Union[int, str]
    ) -> None:
        self.app_name = app_name
        """The name of the app. Should be namespaced to prevent collision."""
        self.app_dir = Path(app_dir)
        """The app data directory. Location is system dependent."""
        self.schema_url = schema_url
        """The url to the current version of the Eve ESI schema."""
        self.log_level = int(log_level)
        log_path = Path(app_dir) / Path("logs")
        self.log_path = log_path
        self.logger = logger_(log_path, "eve_esi_jobs", int(log_level))


def make_config_from_env():
    app_name = os.getenv("PFMSOFT_eve_esi_jobs_APP_NAME", "Pfmsoft-Eve-Esi")
    app_dir = os.getenv(
        "PFMSOFT_eve_esi_jobs_APP_DIR",
        click.get_app_dir(
            os.getenv("PFMSOFT_eve_esi_jobs_APP_NAME", "Pfmsoft-Eve-Esi"),
            force_posix=True,
        ),
    )
    schema_url = os.getenv(
        "PFMSOFT_eve_esi_jobs_SCHEMA_URL",
        "https://esi.evetech.net/latest/swagger.json",
    )
    log_level = os.getenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(logging.INFO))
    config = EveEsiJobConfig(app_name, app_dir, schema_url, log_level)
    return config


logger = logging.getLogger(__name__)


def logger_(test_log_path: Path, logger_name: str, log_level: int):
    log_level = int(log_level)
    log_file_name = f"{logger_name}.log"
    _logger = logging.getLogger(logger_name)
    log_path: Path = test_log_path / Path("esi-logs")
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / Path(log_file_name), maxBytes=102400, backupCount=10
    )
    format_string = (
        "%(asctime)s %(levelname)s:%(funcName)s: "
        "%(message)s [in %(pathname)s:%(lineno)d]"
    )
    file_handler.setFormatter(logging.Formatter(format_string))
    file_handler.setLevel(log_level)
    _logger.addHandler(file_handler)
    # _logger.addHandler(RichHandler()
    _logger.setLevel(log_level)
    ############################################################
    # NOTE add file handler to other library modules as needed #
    ############################################################
    # async_logger = logging.getLogger("eve_esi_jobs")
    # async_logger.addHandler(file_handler)
    # async_logger.setLevel(log_level)
    return _logger
