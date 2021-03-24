# from dataclasses import dataclass, field
# from typing import Any, Dict, List, Sequence, Type, Union

# from pydantic import BaseModel
# from rich import inspect

# from eve_esi_jobs.action_callbacks import SaveResultToFile
# from eve_esi_jobs.actions import EsiProvider
# from eve_esi_jobs.app_config import SCHEMA_URL, logger
# from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
#     AiohttpAction,
#     AiohttpActionCallback,
#     ResponseToJson,
#     ResponseToText,
# )


# @dataclass
# class CallbackManifestEntry:
#     callback: Type[AiohttpActionCallback]
#     valid_targets: List[str] = field(default_factory=list)


# CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
#     "save_json_to_file": CallbackManifestEntry(
#         callback=SaveResultToFile, valid_targets=["success"]
#     ),
#     "response_to_json": CallbackManifestEntry(
#         callback=ResponseToJson, valid_targets=["success"]
#     ),
#     "response_to_text": CallbackManifestEntry(
#         callback=ResponseToText, valid_targets=["success"]
#     ),
# }


# class CallbackJson(BaseModel):
#     callback_id: str
#     args: List[Any] = []
#     kwargs: Dict[str, Any] = {}


# class CallbackCollection(BaseModel):
#     success: List[CallbackJson] = []
#     retry: List[CallbackJson] = []
#     fail: List[CallbackJson] = []


# class ActionJson(BaseModel):
#     op_id: str
#     retry_limit: int
#     parameters: Dict[str, Union[str, int]] = {}
#     result_callbacks: CallbackCollection


# json_action_format = {
#     "op_id": "value",
#     "retry_limit": 1,
#     "parameters": {},
#     "result_callbacks": {
#         "success": [
#             {
#                 "callback_id": "id of callback",
#                 "args": "list of arguments to callback",
#                 "kwargs": {"key1": "value"},
#             }
#         ],
#         "fail": [],
#         "retry": [],
#     },
# }


# def make_action_from_json(
#     action_json_raw: Dict, esi_provider: "EsiProvider"
# ) -> AiohttpAction:
#     action_json: ActionJson = ActionJson(**action_json_raw)
#     # op_id = action_json["op_id"]
#     # path_params = build_path_params(action_json, esi_provider)
#     # query_params = build_query_params(action_json, esi_provider)
#     # action_callbacks = build_action_callbacks(action_json, esi_provider)
#     # retry_limit = action_json["retry_limit"]
#     # request_kwargs = build_request_kwargs(action_json, esi_provider)
#     # context = build_context(action_json, esi_provider)
#     action = esi_provider.build_action(
#         op_id=action_json.op_id,
#         path_params=build_path_params(action_json, esi_provider),
#         query_params=build_query_params(action_json, esi_provider),
#         action_callbacks=build_action_callbacks(action_json, esi_provider),
#         retry_limit=action_json.retry_limit,
#         request_kwargs=build_request_kwargs(action_json, esi_provider),
#         context=build_context(action_json, esi_provider),
#     )
#     return action


# def build_path_params(action_json: ActionJson, esi_provider: EsiProvider) -> Dict:
#     try:
#         path_params = split_parameters(action_json, "path", esi_provider)
#         return path_params
#     except ValueError as ex:
#         logger.warning("Missing required parameter %s", ex)
#         # FIXME what to do about errors
#         return {}


# def split_parameters(
#     action_json: ActionJson, split_id: str, esi_provider: EsiProvider
# ) -> Dict:
#     split_params = {}

#     possible_parameters: Dict = esi_provider.op_id_lookup[action_json.op_id].parameters
#     for param_id, values in possible_parameters.items():
#         param_location = values.get("in", None)
#         if param_location == split_id:
#             required = values.get("required", False)
#             if param_id in action_json.parameters:
#                 # validate params here
#                 split_params[param_id] = action_json.parameters[param_id]
#             else:
#                 if required:
#                     raise ValueError(
#                         f"Missing required parameter {param_id} in {action_json}"
#                     )
#     return split_params


# def build_query_params(action_json: ActionJson, esi_provider: EsiProvider) -> Dict:
#     try:
#         path_params = split_parameters(action_json, "query", esi_provider)
#     except ValueError as ex:
#         logger.warning("Missing required parameter %s", ex)
#     return path_params


# def build_action_callbacks(
#     action_json: ActionJson, esi_provider: EsiProvider
# ) -> Dict[str, Sequence[AiohttpActionCallback]]:
#     callbacks: Dict[str, Sequence[AiohttpActionCallback]] = {
#         "success": [],
#         "retry": [],
#         "fail": [],
#     }
#     callbacks["success"] = build_callback_from_json(
#         "success", action_json.result_callbacks.success
#     )
#     callbacks["retry"] = build_callback_from_json(
#         "retry", action_json.result_callbacks.retry
#     )
#     callbacks["fail"] = build_callback_from_json(
#         "fail", action_json.result_callbacks.fail
#     )
#     # inspect(callbacks)
#     return callbacks


# def build_callback_from_json(
#     target: str, callback_jsons: List[CallbackJson]
# ) -> List[AiohttpActionCallback]:
#     callbacks: List[AiohttpActionCallback] = []
#     for callback_json in callback_jsons:
#         callback_id = callback_json.callback_id
#         manifest_entry = CALLBACK_MANIFEST.get(callback_id, None)
#         if manifest_entry is None:
#             raise ValueError(
#                 f"Unable to find {callback_id} in manifest. Is it a valid callback id?"
#             )
#         if target not in manifest_entry.valid_targets:
#             raise ValueError(
#                 f"Invalid target for {callback_id}. Tried {target}, expected one of {manifest_entry.valid_targets}"
#             )
#         callbacks.append(
#             manifest_entry.callback(*callback_json.args, **callback_json.kwargs)
#         )
#     return callbacks


# def build_request_kwargs(action_json: ActionJson, esi_provider: EsiProvider) -> Dict:
#     # request kwargs include:
#     # params - used to build the query string
#     # data/json - sent in the body of the request
#     # headers
#     # auth? expect to use oauth token
#     request_kwargs = {}
#     query_params = build_query_params(action_json, esi_provider)
#     request_kwargs["params"] = query_params
#     return request_kwargs


# def build_context(action_json: ActionJson, esi_provider: EsiProvider) -> Dict:
#     context = {}
#     context["action_json"] = action_json.dict()
#     return context
