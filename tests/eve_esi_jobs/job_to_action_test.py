import asyncio
import logging

from pfmsoft.aiohttp_queue import AiohttpAction, AiohttpQueueWorkerFactory
from pfmsoft.aiohttp_queue.runners import queue_runner
from rich import inspect

from eve_esi_jobs.eve_esi_jobs import deserialize_json_job
from eve_esi_jobs.job_to_action import JobsToActions


def test_make_action_from_json(esi_provider, caplog):
    caplog.set_level(logging.INFO)
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "result_callbacks": {
            "success": [
                {"callback_id": "response_content_to_json", "args": [], "kwargs": {}}
            ],
            "retry": [],
            "fail": [],
        },
    }
    esi_job = deserialize_json_job(esi_job_json)
    jobs_to_actions = JobsToActions()
    actions = jobs_to_actions.make_actions(
        [esi_job], esi_provider, template_overrides=None
    )
    action = actions[0]
    assert action.url_parameters == {"region_id": 10000002}
    assert action.request_kwargs["params"] == {"type_id": 34}
    assert isinstance(action, AiohttpAction)
    worker = AiohttpQueueWorkerFactory()
    asyncio.run(queue_runner([action], [worker]))
    assert action.result is not None
    assert len(action.result) > 5
    inspect(action.context["esi_job"])


def test_build_path_parameters(esi_provider):
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "result_callbacks": {},
        "additional_results": [],
    }
    esi_job = deserialize_json_job(esi_job_json)
    jobs_to_actions = JobsToActions()
    # pylint: disable=protected-access
    path_params = jobs_to_actions._build_path_params(esi_job, esi_provider)
    # print(path_params)
    assert path_params["region_id"] == esi_job_json["parameters"]["region_id"]
    assert len(list(path_params.keys())) == 1


def test_build_query_parameters(esi_provider):
    esi_job_json = {
        "op_id": "get_markets_region_id_history",
        "retry_limit": 1,
        "parameters": {"region_id": 10000002, "type_id": 34},
        "result_callbacks": {},
        "additional_results": [],
    }
    esi_job = deserialize_json_job(esi_job_json)
    jobs_to_actions = JobsToActions()
    # pylint: disable=protected-access
    query_params = jobs_to_actions._build_query_params(esi_job, esi_provider)
    # print(query_params)
    assert query_params["type_id"] == esi_job_json["parameters"]["type_id"]
    assert len(list(query_params.keys())) == 1
