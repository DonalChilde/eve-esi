import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from rich import inspect, print

from eve_esi_jobs.models import deserialize_json_job

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
    # async_logger = logging.getLogger("eve_esi_jobs")
    # async_logger.addHandler(file_handler)
    return _logger


def test_roundtrip_json(test_app_dir):
    file_path = test_app_dir / Path("data/test.json")
    action_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": "10000002", "type_id": 34},
        "result_callbacks": {
            "success": [
                {"callback_id": "response_to_json", "args": [], "kwargs": {}},
                {
                    "callback_id": "save_json_to_file",
                    "kwargs": {"file_path": file_path},
                    "args": [],
                },
            ],
            "retry": [],
            "fail": [],
        },
    }
    deserialized = deserialize_json_job(action_json)
    print(deserialized)
    print(deserialized.json(indent=2))
    assert deserialized.op_id == action_json["op_id"]
    assert deserialized.retry_limit == action_json["retry_limit"]
    assert deserialized.parameters == action_json["parameters"]
    assert deserialized.result_callbacks == action_json["result_callbacks"]
    serialized = deserialized.dict()
    assert serialized["op_id"] == action_json["op_id"]
    assert serialized["retry_limit"] == action_json["retry_limit"]
    assert serialized["parameters"] == action_json["parameters"]
