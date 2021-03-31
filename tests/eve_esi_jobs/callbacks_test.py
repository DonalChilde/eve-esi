import asyncio
from pathlib import Path

from pfmsoft.aiohttp_queue import AiohttpQueueWorkerFactory
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.eve_esi_jobs import deserialize_json_job
from eve_esi_jobs.job_to_action import make_action_from_job


def test_save_job_to_file(esi_provider, test_app_dir):

    file_path: Path = test_app_dir / Path("data/test.json")
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "result_callbacks": {
            "success": [
                {"callback_id": "result_to_json"},
                {
                    "callback_id": "save_result_to_json_file",
                    "kwargs": {"file_path": file_path},
                },
            ]
        },
    }
    esi_job = deserialize_json_job(esi_job_json)
    action = make_action_from_job(esi_job, esi_provider)
    worker = AiohttpQueueWorkerFactory()
    asyncio.run(queue_runner([action], [worker]))
    assert action.result is not None
    assert len(action.result) > 5
    keys = ["average", "date", "highest", "lowest", "order_count", "volume"]
    assert all(key in keys for key in action.result[0])
    assert action.context["esi_job"].op_id == "get_markets_region_id_history"
    assert file_path.exists()
    assert file_path.stat().st_size > 10
