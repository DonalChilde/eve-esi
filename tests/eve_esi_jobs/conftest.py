""" fixtures """
import json
import logging
from importlib import resources
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import pytest
from rich import inspect

from eve_esi_jobs import logger as app_logger
from eve_esi_jobs.esi_provider import EsiProvider

APP_LOG_LEVEL = logging.INFO


@pytest.fixture(scope="session", name="logger")
def logger_(test_log_path):
    log_level = logging.DEBUG
    log_file_name = f"{__name__}.log"
    _logger = logging.getLogger(__name__)
    log_dir_path: Path = test_log_path / Path("test-logs")
    log_dir_path.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir_path / Path(log_file_name)
    handler = file_handler(log_file_path)
    _logger.addHandler(handler)
    _logger.setLevel(log_level)
    ############################################################
    # NOTE add file handler to other library modules as needed #
    ############################################################
    # async_logger = logging.getLogger("eve_esi_jobs")
    # async_logger.addHandler(file_handler)
    # async_logger.setLevel(log_level)
    return _logger


def file_handler(
    file_path: Path,
    log_level: int = logging.WARNING,
    format_string: Optional[str] = None,
):
    handler = RotatingFileHandler(file_path, maxBytes=102400, backupCount=10)
    format_string = (
        "%(asctime)s %(levelname)s:%(funcName)s: "
        "%(message)s [in %(pathname)s:%(lineno)d]"
    )
    handler.setFormatter(logging.Formatter(format_string))
    handler.setLevel(log_level)
    return handler


@pytest.fixture(scope="session")
def esi_provider(esi_schema):
    # logger = logger_(test_log_path)
    # schema = load_schema("latest")
    provider: EsiProvider = EsiProvider(esi_schema)
    assert provider.schema is not None
    assert provider.schema["basePath"] == "/latest"
    # logger.info(
    #     "created esi_provider with schema version: %s",
    #     provider.schema["info"]["version"],
    # )
    assert provider.schema_version == "1.7.15"
    return provider


@pytest.fixture(scope="session", name="test_log_path")
def test_log_path_(test_app_dir):
    log_path = test_app_dir / Path("test-logs")
    print(f"Logging at: {log_path}")
    return log_path


@pytest.fixture(scope="session", name="test_app_dir")
def test_app_dir_(tmp_path_factory):
    app_dir_path = tmp_path_factory.mktemp("eve-esi-")
    return app_dir_path


@pytest.fixture(scope="session", name="esi_schema")
def esi_schema_(logger) -> dict:
    try:
        resource_path: str = "tests.eve_esi_jobs.resources.schema"
        resource_name: str = "esi_schema_1.7.15.json"
        with resources.open_text(resource_path, resource_name) as schema_file:
            schema = json.load(schema_file)
            logger.info("Loaded resource file %s from %s", resource_name, resource_path)
            return schema
    except Exception as ex:
        logger.exception(
            "Unable to load resource file %s from %s Error msg %s",
            resource_name,
            resource_path,
            ex,
        )
        raise ex


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, test_app_dir):
    # app_logger.setLevel(APP_LOG_LEVEL)
    # for handler in app_logger.handlers:
    #     if isinstance(handler, logging.FileHandler):
    #         app_logger.handlers.remove(handler)
    #     handler.setLevel(APP_LOG_LEVEL)

    # print("In test env setup")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_TESTING", "True")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(APP_LOG_LEVEL))
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_APP_DIR", str(test_app_dir))
    # log_file_path = test_app_dir / Path("esi-test.log")
    # new_handler = file_handler(log_file_path, log_level=APP_LOG_LEVEL)
    # app_logger.addHandler(new_handler)
    # inspect(app_logger)
