import asyncio

from rich import inspect

from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpQueueWorker,
    ResponseToJson,
    do_aiohttp_action_queue,
)


def test_get_action(esi_provider):
    """Testing that AiohttpAction works.

    Also example of how to use.
    """

    op_id = "get_markets_region_id_history"
    path_params = {"region_id": 10000002}
    query_params = {"type_id": 34}
    action_callbacks = {"success": [ResponseToJson()]}
    action = esi_provider.build_action(
        op_id, path_params, query_params, action_callbacks=action_callbacks
    )
    inspect(action)
    assert action is not None
    worker = AiohttpQueueWorker()
    asyncio.run(do_aiohttp_action_queue([action], [worker]))
    assert action.result is not None
    assert len(action.result) > 5
