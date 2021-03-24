# import asyncio
# import logging
# import os
# from logging.handlers import RotatingFileHandler
# from pathlib import Path

# import pytest
# from rich import inspect, print

# from eve_esi import action_callbacks
# from eve_esi import action_callbacks as AC
# from eve_esi import action_json as AJ
# from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
#     AiohttpAction,
#     AiohttpQueueWorker,
#     do_aiohttp_action_queue,
# )

# LOG_LEVEL = logging.INFO


# @pytest.fixture(scope="module")
# def logger(test_log_path):
#     log_file_name = f"{__name__}.log"
#     _logger = logging.getLogger(__name__)
#     if not os.path.exists(test_log_path):
#         os.mkdir(test_log_path)
#     file_handler = RotatingFileHandler(
#         test_log_path / Path(log_file_name), maxBytes=102400, backupCount=10
#     )
#     format_string = "%(asctime)s %(levelname)s:%(funcName)s: %(message)s [in %(pathname)s:%(lineno)d]"
#     file_handler.setFormatter(logging.Formatter(format_string))
#     file_handler.setLevel(LOG_LEVEL)
#     _logger.addHandler(file_handler)
#     _logger.setLevel(LOG_LEVEL)
#     ############################################################
#     # NOTE add file handler to other library modules as needed #
#     ############################################################
#     # async_logger = logging.getLogger("eve_esi")
#     # async_logger.addHandler(file_handler)
#     return _logger


# def test_make_action_from_json(esi_provider, test_app_dir):
#     file_path = test_app_dir / Path("data/test.json")
#     action_json = {
#         "op_id": "get_markets_region_id_history",
#         "retry_limit": 1,
#         "parameters": {"region_id": 10000002, "type_id": 34},
#         "result_callbacks": {
#             "success": [
#                 {"callback_id": "response_to_json"},
#                 {
#                     "callback_id": "save_json_to_file",
#                     "kwargs": {"file_path": file_path},
#                 },
#             ]
#         },
#     }

#     action = AJ.make_action_from_json(action_json, esi_provider)
#     assert action.url_parameters == {"region_id": "10000002"}
#     assert action.request_kwargs["params"] == {"type_id": "34"}
#     assert isinstance(action, AiohttpAction)
#     worker = AiohttpQueueWorker()
#     asyncio.run(do_aiohttp_action_queue([action], [worker]))
#     assert action.result is not None
#     assert len(action.result) > 5
#     keys = ["average", "date", "highest", "lowest", "order_count", "volume"]
#     assert all(key in keys for key in action.result[0])
#     # inspect(action.action_callbacks)
#     assert action.context["action_json"]["op_id"] == "get_markets_region_id_history"


# def test_action_json_deserialize(test_app_dir):
#     file_path = test_app_dir / Path("data/test.json")
#     action_json = {
#         "op_id": "get_markets_region_id_history",
#         "retry_limit": 1,
#         "parameters": {"region_id": 10000002, "type_id": 34},
#         "result_callbacks": {
#             "success": [
#                 {"callback_id": "response_to_json"},
#                 {
#                     "callback_id": "save_json_to_file",
#                     "kwargs": {"file_path": file_path},
#                 },
#             ]
#         },
#     }
#     deserialized = AJ.ActionJson(**action_json)
#     print(deserialized)
#     print(deserialized.json(indent=2))
#     assert deserialized.op_id == "get_markets_region_id_history"
