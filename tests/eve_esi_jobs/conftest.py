""" fixtures """
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from eve_esi_jobs.app_data import load_schema
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.pfmsoft.util.file.read_write import load_json

# def logger_(test_log_path):
#     log_file_name = f"{__name__}.log"
#     _logger = logging.getLogger(__name__)
#     log_path = test_log_path / Path("test-logs")
#     log_level = logging.DEBUG
#     if not os.path.exists(log_path):
#         os.mkdir(log_path)
#     file_handler = RotatingFileHandler(
#         log_path / Path(log_file_name), maxBytes=102400, backupCount=10
#     )
#     format_string = "%(asctime)s %(levelname)s:%(funcName)s: %(message)s [in %(pathname)s:%(lineno)d]"
#     file_handler.setFormatter(logging.Formatter(format_string))
#     file_handler.setLevel(log_level)
#     _logger.addHandler(file_handler)
#     _logger.setLevel(log_level)
#     ############################################################
#     # NOTE add file handler to other library modules as needed #
#     ############################################################
#     # async_logger = logging.getLogger("eve_esi_jobs")
#     # async_logger.addHandler(file_handler)
#     return _logger


APP_LOG_LEVEL = logging.INFO


@pytest.fixture(scope="session")
def esi_provider(test_log_path):
    # logger = logger_(test_log_path)
    schema = load_schema("latest")
    provider: EsiProvider = EsiProvider(schema)
    assert provider.schema is not None
    assert provider.schema["basePath"] == "/latest"
    # logger.info(
    #     "created esi_provider with schema version: %s",
    #     provider.schema["info"]["version"],
    # )
    assert provider.schema_version() == "1.7.15"
    return provider


@pytest.fixture(scope="session")
def test_log_path(test_app_dir):
    log_path = test_app_dir / Path("test-logs")
    print(f"Logging at: {log_path}")
    return log_path


@pytest.fixture(scope="session")
def test_app_dir(tmp_path_factory):
    app_dir_path = tmp_path_factory.mktemp("eve-esi-")
    return app_dir_path


# @pytest.fixture(scope="class")
# def load_schema() -> dict:
#     # TODO this needs to handle loading from a testing resource
#     file_path = Path(
#         "/home/chad/.eve-esi/static/schemas/schema-1.7.15/schema-1.7.15.json"
#     )
#     schema = load_json(file_path)
#     return schema


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, test_app_dir):
    print("In test env setup")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_TESTING", "True")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(APP_LOG_LEVEL))
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_APP_DIR", str(test_app_dir))
