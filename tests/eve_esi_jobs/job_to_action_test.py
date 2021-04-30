import asyncio
import logging

from pfmsoft.aiohttp_queue import AiohttpAction, AiohttpQueueWorker
from pfmsoft.aiohttp_queue.runners import single_action_runner
from rich import inspect

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import new_manifest
from eve_esi_jobs.job_to_action import JobsToActions
from eve_esi_jobs.operation_manifest import OperationManifest


def test_make_action_from_json(operation_manifest: OperationManifest, caplog):
    caplog.set_level(logging.INFO)
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "max_attempts": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json", "args": [], "kwargs": {}}
            ],
            "retry": [],
            "fail": [],
        },
    }
    esi_job = models.EsiJob.deserialize_obj(esi_job_json)
    callback_provider = new_manifest()
    action = JobsToActions().make_action(
        esi_job=esi_job,
        operation_manifest=operation_manifest,
        callback_manifest=callback_provider,
    )

    assert action.aiohttp_args.params == {"type_id": 34}
    assert isinstance(action, AiohttpAction)
    asyncio.run(single_action_runner(action))
    assert action.response.status == 200
    assert action.response_data is not None
    assert len(action.response_data) > 5
    inspect(action.context["esi_job"])
