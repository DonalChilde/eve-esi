""" fixtures """
import json
import logging
from dataclasses import dataclass
from importlib import resources
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from rich import inspect

from eve_esi_jobs import logger as app_logger
from eve_esi_jobs.esi_provider import EsiProvider

APP_LOG_LEVEL = logging.INFO


@dataclass
class FileResource:
    file_path: Path
    data: Any


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
    provider: EsiProvider = EsiProvider(esi_schema.data)
    assert provider.schema is not None
    assert provider.schema["basePath"] == "/latest"
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


@pytest.fixture(scope="session", name="sample_data")
def sample_data_(logger) -> Dict[str, FileResource]:
    resource_path: str = "tests.eve_esi_jobs.resources.data"
    resource_names = [
        "3-market-history-params-extras.csv",
        "3-market-history-params-extras.json",
        "3-market-history-params.csv",
        "3-market-history-params.json",
        "3-type-ids.csv",
        "3-type-ids.json",
        "3-wrong-params.csv",
        "3-wrong-params.json",
        "json-dict.json",
        "empty-list.json",
    ]
    sample_data = {}
    for resource_name in resource_names:
        file_resource = make_file_resource(
            resource_path=resource_path, resource_name=resource_name, logger=logger
        )
        sample_data[file_resource.file_path.name] = file_resource
    return sample_data


def make_file_resource(resource_path, resource_name, logger) -> FileResource:
    try:
        with resources.path(resource_path, resource_name) as data_path:
            data = data_path.read_text()
            logger.debug(
                "Loaded resource file %s from %s", resource_name, resource_path
            )
            return FileResource(file_path=data_path, data=data)
    except Exception as ex:
        logger.exception(
            "Unable to load resource file %s from %s Error msg %s",
            resource_name,
            resource_path,
            ex,
        )
        raise ex


@pytest.fixture(scope="session", name="esi_schema")
def esi_schema_(logger) -> FileResource:
    resource_path: str = "tests.eve_esi_jobs.resources.schema"
    resource_name: str = "esi_schema_1.7.15.json"
    file_resource = make_file_resource(
        resource_path=resource_path, resource_name=resource_name, logger=logger
    )
    json_data = json.loads(file_resource.data)
    file_resource.data = json_data
    return file_resource


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, test_app_dir):
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_TESTING", "True")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(APP_LOG_LEVEL))
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_APP_DIR", str(test_app_dir))
