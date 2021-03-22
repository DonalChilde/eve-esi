from typing import Dict, List, Sequence

from rich import inspect

from eve_esi.actions import DEFAULT_CALLBACKS, EsiProvider
from eve_esi.app_config import SCHEMA_URL, logger
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
)


def json_action_example():
    action = {
        "op_id": "value",
        "retry_limit": 1,
        "parameters": {},
        "result_callbacks": {},
        "additional_results": [],
    }


def make_action_from_json(
    action_json: Dict, esi_provider: "EsiProvider"
) -> AiohttpAction:
    op_id = action_json["op_id"]
    path_params = build_path_params(action_json, esi_provider)
    query_params = build_query_params(action_json, esi_provider)
    action_callbacks = build_action_callbacks(action_json, esi_provider)
    retry_limit = action_json["retry_limit"]
    request_kwargs = build_request_kwargs(action_json, esi_provider)
    context = build_context(action_json, esi_provider)
    action = esi_provider.build_action(
        op_id=op_id,
        path_params=path_params,
        query_params=query_params,
        action_callbacks=action_callbacks,
        retry_limit=retry_limit,
        request_kwargs=request_kwargs,
        context=context,
    )
    return action


def build_path_params(action_json: Dict, esi_provider: EsiProvider) -> Dict:
    try:
        path_params = split_parameters(action_json, "path", esi_provider)
        return path_params
    except ValueError as ex:
        logger.warning("Missing required parameter %s", ex)


def split_parameters(
    action_json: Dict, split_id: str, esi_provider: EsiProvider
) -> Dict:
    split_params = {}
    op_id = action_json["op_id"]
    action_parameters: Dict = action_json["parameters"]
    possible_parameters: Dict = esi_provider.op_id_lookup[op_id]["parameters"]
    for param_id, values in possible_parameters.items():
        param_location = values.get("in", None)
        if param_location == split_id:
            required = values.get("required", False)
            if param_id in action_parameters:
                # validate params here
                split_params[param_id] = action_parameters[param_id]
            else:
                if required:
                    raise ValueError(
                        f"Missing required parameter {param_id} in {action_json}"
                    )
    return split_params


def build_query_params(action_json: Dict, esi_provider: EsiProvider) -> Dict:
    try:
        path_params = split_parameters(action_json, "query", esi_provider)
    except ValueError as ex:
        logger.warning("Missing required parameter %s", ex)
    return path_params


def build_action_callbacks(
    action_json: Dict, esi_provider: EsiProvider
) -> Dict[str, Sequence[AiohttpActionCallback]]:
    return DEFAULT_CALLBACKS


def build_request_kwargs(action_json: Dict, esi_provider: EsiProvider) -> Dict:
    # request kwargs include:
    # params - used to build the query string
    # data/json - sent in the body of the request
    # headers
    # auth? expect to use oauth token
    request_kwargs = {}
    query_params = build_query_params(action_json, esi_provider)
    request_kwargs["params"] = query_params
    return request_kwargs


def build_context(action_json: Dict, esi_provider: EsiProvider) -> Dict:
    context = {}
    context["action_json"] = action_json
    return context
