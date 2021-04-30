import asyncio
from pathlib import Path

from pfmsoft.aiohttp_queue import AiohttpQueueWorker
from pfmsoft.aiohttp_queue.runners import single_action_runner
from rich import inspect

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import new_manifest
from eve_esi_jobs.job_to_action import JobsToActions


def test_save_job_to_file(operation_manifest, test_app_dir):

    file_path: Path = test_app_dir / Path("data/test.json")
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "max_attempts": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json"},
                {
                    "callback_id": "save_result_to_json_file",
                    "kwargs": {"file_path_template": file_path},
                },
            ]
        },
    }
    # inspect(operation_manifest)
    esi_job = models.EsiJob.deserialize_obj(esi_job_json)
    action = JobsToActions().make_action(
        esi_job=esi_job, operation_manifest=operation_manifest
    )
    asyncio.run(single_action_runner(action))
    assert action.response_data is not None
    assert len(action.response_data) > 5
    keys = ["average", "date", "highest", "lowest", "order_count", "volume"]
    assert all(key in keys for key in action.response_data[0])
    assert action.context["esi_job"].op_id == "get_markets_region_id_history"
    assert file_path.exists()
    assert file_path.stat().st_size > 10
