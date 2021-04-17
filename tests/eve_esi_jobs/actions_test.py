import asyncio

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpQueueWorker
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import queue_runner
from rich import inspect

from eve_esi_jobs.esi_provider import EsiProvider


def test_get_action(esi_provider: EsiProvider):
    """Testing that AiohttpAction works.

    Also example of how to use.
    """

    op_id = "get_markets_region_id_history"
    path_params = {"region_id": 10000002}
    query_params = {"type_id": 34}
    callbacks = ActionCallbacks(success=[ResponseContentToJson()])
    action = esi_provider.build_action_from_op_id(
        op_id, path_params, query_params, callbacks=callbacks
    )
    inspect(action)
    assert action is not None
    worker = AiohttpQueueWorker()
    asyncio.run(queue_runner([action], [worker]))
    assert action.result is not None
    assert len(action.result) > 5
