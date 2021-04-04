""" fixtures """
import json
import logging
from dataclasses import dataclass
from importlib import resources
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from rich import inspect

from eve_esi_jobs import logger as app_logger
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import optional_object

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
def sample_data_() -> Dict[str, FileResource]:
    resource_path: str = "tests.eve_esi_jobs.resources.data"
    sample_data = make_file_resources_from_resource_path(resource_path)
    return sample_data


@pytest.fixture(scope="session", name="work_orders")
def work_orders_() -> Dict[str, FileResource]:
    resource_path: str = "tests.eve_esi_jobs.resources.work_orders"
    sample_data = make_file_resources_from_resource_path(resource_path)
    return sample_data


def make_file_resources_from_resource_path(
    resource_path, exclude_suffixes: Optional[List[str]] = None
):
    file_paths = collect_resource_paths(resource_path, exclude_suffixes)
    file_resources = {}
    for file_path in file_paths:
        data = file_path.read_text()
        file_resource = FileResource(file_path=file_path, data=data)
        file_resources[file_path.name] = file_resource
    assert "__init__.py" not in file_resources
    return file_resources


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


def collect_resource_paths(
    resource_path: str,
    exclude_suffixes: Optional[List[str]] = None,
) -> List[Path]:
    exclude_suffixes = optional_object(exclude_suffixes, list)
    result = []
    with resources.path(resource_path, "__init__.py") as data_path:
        files = data_path.parent.glob("*.*")
        for file in files:
            if file.name != "__init__.py" and file.suffix not in exclude_suffixes:
                result.append(file)
    return result


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
