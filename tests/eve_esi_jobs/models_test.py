import logging
from pathlib import Path

from eve_esi_jobs.eve_esi_jobs import (
    deserialize_json_job,
    deserialize_json_work_order,
    serialize_job,
    serialize_work_order,
)
from eve_esi_jobs.sample_work_orders import result_and_response_to_job_json_file

# import pytest
# from rich import inspect, print


LOG_LEVEL = logging.INFO


def test_roundtrip_json_job(test_app_dir):
    # caplog.set_level(logging.INFO)
    file_path = test_app_dir / Path("data/test.json")
    action_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": "10000002", "type_id": 34},
        "result_callbacks": {
            "success": [
                {
                    "callback_id": "result_to_json",
                    "args": [],
                    "kwargs": {},
                    "config": {},
                },
                {
                    "callback_id": "save_json_to_file",
                    "kwargs": {"file_path": file_path},
                    "args": [],
                    "config": {},
                },
            ],
            "retry": [],
            "fail": [],
        },
    }
    deserialized = deserialize_json_job(action_json)
    assert deserialized.op_id == action_json["op_id"]
    assert deserialized.retry_limit == action_json["retry_limit"]
    assert deserialized.parameters == action_json["parameters"]
    assert deserialized.result_callbacks == action_json["result_callbacks"]
    serialized = serialize_job(deserialized)
    assert serialized["op_id"] == action_json["op_id"]
    assert serialized["retry_limit"] == action_json["retry_limit"]
    assert serialized["parameters"] == action_json["parameters"]
    assert serialized["result_callbacks"] == action_json["result_callbacks"]


def test_roundtrip_work_order():
    ewo = result_and_response_to_job_json_file()
    serialized = serialize_work_order(ewo)
    deserialized = deserialize_json_work_order(serialized)
    assert ewo == deserialized
    assert ewo.dict() == serialized
