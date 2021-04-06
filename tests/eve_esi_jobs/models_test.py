import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from rich import inspect

import eve_esi_jobs.eve_esi_jobs as EJ
from eve_esi_jobs import models
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
                    "kwargs": {"file_path": str(file_path)},
                    "args": [],
                    "config": {},
                },
            ],
            "retry": [],
            "fail": [],
        },
    }
    deserialized = EJ.deserialize_job_from_dict(action_json)
    assert deserialized.op_id == action_json["op_id"]
    assert deserialized.retry_limit == action_json["retry_limit"]
    assert deserialized.parameters == action_json["parameters"]
    assert deserialized.result_callbacks == action_json["result_callbacks"]
    serialized = EJ.serialize_job(deserialized)
    print(serialized)
    as_job = EJ.deserialize_job_from_string(serialized)
    assert as_job.op_id == deserialized.op_id
    assert as_job.result_callbacks == deserialized.result_callbacks
    assert as_job.uid == deserialized.uid
    assert isinstance(as_job.uid, UUID)


def test_roundtrip_work_order():
    ewo = result_and_response_to_job_json_file()
    serialized = EJ.serialize_work_order(ewo)
    deserialized = EJ.deserialize_work_order_from_string(serialized)
    assert ewo == deserialized
    # uuids serialize as strings, and are made back into uuids
    # in the model, not the json
    assert ewo.dict() != json.loads(serialized)


def test_job_callback():
    callback_json = {
        "success": [
            {
                "callback_id": "result_to_json",
                "args": [],
                "kwargs": {},
                "config": {},
            },
            {
                "callback_id": "save_json_to_file",
                "kwargs": {"file_path": "file_path"},
                "args": [],
                "config": {},
            },
        ],
        "retry": [],
        "fail": [],
    }
    result_callback = models.CallbackCollection(**callback_json)
    assert len(result_callback.success) == 2
    callback_json_2 = {
        "success": [
            {"callback_id": "result_to_json"},
            {"callback_id": "save_json_to_file", "kwargs": {"file_path": "file_path"}},
        ]
    }
    result_callback_2 = models.CallbackCollection(**callback_json_2)
    assert result_callback == result_callback_2
    dict_1 = result_callback.dict()
    dict_2 = result_callback_2.dict()
    inspect(dict_1)
    inspect(dict_2)
    assert dict_1 == dict_2


def test_get_iso_time():
    print(datetime.now().isoformat().replace(":", "-"))
