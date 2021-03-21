import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from rich import inspect, print

from eve_esi.actions import EsiProvider
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpQueueWorker,
    ResponseToJson,
    do_aiohttp_action_queue,
)
from eve_esi.pfmsoft.util.file.read_write import load_json

LOG_LEVEL = logging.INFO


@pytest.fixture(scope="module")
def logger(test_log_path):
    log_file_name = f"{__name__}.log"
    _logger = logging.getLogger(__name__)
    if not os.path.exists(test_log_path):
        os.mkdir(test_log_path)
    file_handler = RotatingFileHandler(
        test_log_path / Path(log_file_name), maxBytes=102400, backupCount=10
    )
    format_string = "%(asctime)s %(levelname)s:%(funcName)s: %(message)s [in %(pathname)s:%(lineno)d]"
    file_handler.setFormatter(logging.Formatter(format_string))
    file_handler.setLevel(LOG_LEVEL)
    _logger.addHandler(file_handler)
    _logger.setLevel(LOG_LEVEL)
    ############################################################
    # NOTE add file handler to other library modules as needed #
    ############################################################
    # async_logger = logging.getLogger("eve_esi")
    # async_logger.addHandler(file_handler)
    return _logger


def test_load_schema(load_schema, logger):
    esi_provider = EsiProvider(load_schema)
    assert esi_provider.schema is not None
    assert esi_provider.schema["basePath"] == "/latest"
    logger.info(
        "created esi_provider with schema version: %s",
        esi_provider.schema["info"]["version"],
    )


def test_get_action(load_schema):
    esi_provider = EsiProvider(load_schema)
    op_id = "get_markets_region_id_history"
    path_params = {"region_id": 10000002}
    query_params = {"type_id": 34}
    action_callbacks = {"success": [ResponseToJson()]}
    action = esi_provider.build_action(
        op_id, path_params, query_params, action_callbacks=action_callbacks
    )
    inspect(action)
    assert action is not None
    worker = AiohttpQueueWorker()
    asyncio.run(do_aiohttp_action_queue([action], [worker]))
    assert action.result is not None
    assert len(action.result) > 5
