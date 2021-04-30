import asyncio
from string import Template

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpQueueWorker
from pfmsoft.aiohttp_queue.aiohttp import AiohttpAction, AiohttpRequest
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import queue_runner
from rich import inspect

from eve_esi_jobs.operation_manifest import OperationManifest


def test_get_action(operation_manifest: OperationManifest):
    """Testing that AiohttpAction works.

    Also example of how to use.
    """

    op_id = "get_markets_region_id_history"
    url_template = Template(operation_manifest.url_template(op_id))
    path_params = {"region_id": 10000002}
    query_params = {"type_id": 34}
    url = url_template.substitute(path_params)
    aiohttp_args = AiohttpRequest(method="get", url=url, params=query_params)
    callbacks = ActionCallbacks(success=[ResponseContentToJson()])
    action = AiohttpAction(aiohttp_args=aiohttp_args, callbacks=callbacks)
    inspect(action)
    assert action is not None
    worker = AiohttpQueueWorker()
    asyncio.run(queue_runner([action], [worker]))
    assert action.response_data is not None
    assert len(action.response_data) > 5
