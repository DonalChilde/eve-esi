import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from rich import inspect

# import eve_esi_jobs.eve_esi_jobs as EJ
from eve_esi_jobs import models
from eve_esi_jobs.examples.work_orders import result_and_response_to_job_json_file

# import pytest
# from rich import inspect, print


LOG_LEVEL = logging.INFO


def test_roundtrip_json_job(test_app_dir):
    # caplog.set_level(logging.INFO)
    file_path = test_app_dir / Path("data/test.json")
    job_json = {
        "op_id": "get_markets_region_id_history",
        "max_attempts": 1,
        "parameters": {"region_id": "10000002", "type_id": 34},
        "callbacks": {
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
    deserialized = models.EsiJob.deserialize_obj(job_json)
    assert deserialized.op_id == job_json["op_id"]
    assert deserialized.max_attempts == job_json["max_attempts"]
    assert deserialized.parameters == job_json["parameters"]
    assert deserialized.callbacks == job_json["callbacks"]
    json_string = deserialized.serialize_json()
    # print(serialized)
    as_job = models.EsiJob.deserialize_json(json_string)
    assert as_job.op_id == deserialized.op_id
    assert as_job.callbacks == deserialized.callbacks
    assert as_job.uid == deserialized.uid
    assert isinstance(as_job.uid, UUID)
    # assert False


def test_roundtrip_work_order():
    ewo = result_and_response_to_job_json_file()

    json_string = ewo.serialize_json()
    deserialized = models.EsiWorkOrder.deserialize_json(json_string)
    assert ewo == deserialized
    # uuids serialize as strings, and are made back into uuids
    # in the model, not the json
    assert ewo.dict() != json.loads(json_string)
    # assert False


def test_serialize_mixin():
    ewo = result_and_response_to_job_json_file()
    json_string = ewo.serialize_json()
    yaml_string = ewo.serialize_yaml()
    ewo_from_json = ewo.deserialize_json(json_string)
    ewo_from_yaml = ewo.deserialize_yaml(yaml_string)
    assert ewo_from_json == ewo_from_yaml
    assert ewo == ewo_from_json
    assert ewo == ewo_from_yaml
    json_obj = json.loads(json_string)
    ewo_from_json_obj = models.EsiWorkOrder.deserialize_obj(json_obj)
    assert ewo_from_json_obj == ewo
    ewo_from_json_obj.name = "new name"
    assert ewo_from_json_obj != ewo


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
    result_callback = models.CallbackCollection.deserialize_obj(callback_json)
    assert len(result_callback.success) == 2
    callback_json_2 = {
        "success": [
            {"callback_id": "result_to_json"},
            {"callback_id": "save_json_to_file", "kwargs": {"file_path": "file_path"}},
        ]
    }
    result_callback_2 = models.CallbackCollection.deserialize_obj(callback_json_2)
    assert result_callback == result_callback_2
    dict_1 = result_callback.dict()
    dict_2 = result_callback_2.dict()
    # inspect(dict_1)
    # inspect(dict_2)
    assert dict_1 == dict_2


def test_get_iso_time():
    print(datetime.now().isoformat().replace(":", "-"))
