import asyncio
from pathlib import Path

import pytest
from rich import inspect, print

# from eve_esi.actions import EsiProvider
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpQueueWorker,
    ResponseToJson,
    do_aiohttp_action_queue,
)
from eve_esi.pfmsoft.util.file.read_write import load_json


@pytest.fixture(scope="class")
def load_schema() -> dict:
    file_path = Path("/home/chad/.eve-esi/schema/esi_schema.json")
    schema = load_json(file_path)
    return schema


# def test_load_schema(load_schema):
#     esi_provider = EsiProvider(load_schema)
#     assert esi_provider.schema is not None
#     assert esi_provider.schema["basePath"] == "/latest"


# def test_get_action(load_schema):
#     esi_provider = EsiProvider(load_schema)
#     op_id = "get_markets_region_id_history"
#     path_params = {"region_id": 10000002}
#     query_params = {"type_id": 34}
#     action_callbacks = {"success": [ResponseToJson()]}
#     action = esi_provider.build_action(
#         op_id, path_params, query_params, action_callbacks=action_callbacks
#     )
#     inspect(action)
#     assert action is not None
#     worker = AiohttpQueueWorker()
#     asyncio.run(do_aiohttp_action_queue([action], [worker]))
#     assert action.result is not None
#     assert len(action.result) > 5
