from typing import Any, Dict, List, Optional, Sequence

from rich import inspect

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.models import CALLBACK_MANIFEST, EsiJob, JobCallback
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
)

# FIXME default file name:${op_id}-${path parameters alpha sort?}-${isodate nanosecond}


def make_action_from_job(esi_job: EsiJob, esi_provider: EsiProvider) -> AiohttpAction:
    action = esi_provider.build_action(
        op_id=esi_job.op_id,
        path_params=build_path_params(esi_job, esi_provider),
        query_params=build_query_params(esi_job, esi_provider),
        action_callbacks=build_action_callbacks(esi_job, esi_provider),
        retry_limit=esi_job.retry_limit,
        request_kwargs=build_request_kwargs(esi_job, esi_provider),
        context=build_context(esi_job, esi_provider),
    )
    return action


def build_path_params(esi_job: EsiJob, esi_provider: EsiProvider) -> Dict:
    try:
        path_params = split_parameters(esi_job, "path", esi_provider)
        return path_params
    except ValueError as ex:
        logger.warning("Missing required parameter %s", ex)
        # FIXME what to do about errors
        return {}


def split_parameters(esi_job: EsiJob, split_id: str, esi_provider: EsiProvider) -> Dict:
    split_params = {}

    possible_parameters: Dict = esi_provider.op_id_lookup[esi_job.op_id].parameters
    for param_id, values in possible_parameters.items():
        param_location = values.get("in", None)
        if param_location == split_id:
            required = values.get("required", False)
            if param_id in esi_job.parameters:
                # validate params here
                split_params[param_id] = esi_job.parameters[param_id]
            else:
                if required:
                    raise ValueError(
                        f"Missing required parameter {param_id} in {esi_job}"
                    )
    return split_params


def build_query_params(action_json: EsiJob, esi_provider: EsiProvider) -> Dict:
    try:
        path_params = split_parameters(action_json, "query", esi_provider)
    except ValueError as ex:
        logger.warning("Missing required parameter %s", ex)
    return path_params


def build_action_callbacks(
    esi_job: EsiJob, esi_provider: EsiProvider
) -> Dict[str, Sequence[AiohttpActionCallback]]:
    callbacks: Dict[str, Sequence[AiohttpActionCallback]] = {
        "success": [],
        "retry": [],
        "fail": [],
    }
    callbacks["success"] = build_target_callbacks(
        "success", esi_job.result_callbacks.success
    )
    callbacks["retry"] = build_target_callbacks("retry", esi_job.result_callbacks.retry)
    callbacks["fail"] = build_target_callbacks("fail", esi_job.result_callbacks.fail)
    # inspect(callbacks)
    return callbacks


def build_target_callbacks(
    target: str, job_callbacks: List[JobCallback]
) -> List[AiohttpActionCallback]:
    callbacks: List[AiohttpActionCallback] = []
    for job_callback in job_callbacks:
        callback_id = job_callback.callback_id
        manifest_entry = CALLBACK_MANIFEST.get(callback_id, None)
        if manifest_entry is None:
            raise ValueError(
                f"Unable to find {callback_id} in manifest. Is it a valid callback id?"
            )
        if target not in manifest_entry.valid_targets:
            raise ValueError(
                f"Invalid target for {callback_id}. Tried {target}, expected one of {manifest_entry.valid_targets}"
            )
        try:
            callback = manifest_entry.callback(
                *job_callback.args, **job_callback.kwargs
            )
            callbacks.append(callback)
        except Exception as ex:
            # FIXME proper Exception
            logger.exception(
                f"Failed to initialize callback with {job_callback}. Did you supply the correct arguments?"
            )
    return callbacks


def build_headers(esi_job: EsiJob, esi_provider: EsiProvider) -> Optional[Dict]:
    headers: Dict = {}

    if not headers:
        return None
    return headers


def build_request_kwargs(esi_job: EsiJob, esi_provider: EsiProvider) -> Dict[str, Any]:
    # request kwargs include:
    # params - used to build the query string
    # data/json - sent in the body of the request
    # headers
    # auth? expect to use oauth token
    request_kwargs: Dict[str, Any] = {}
    request_kwargs["params"] = build_query_params(esi_job, esi_provider)
    request_kwargs["params"] = build_headers(esi_job, esi_provider)
    return request_kwargs


def build_context(esi_job: EsiJob, esi_provider: EsiProvider) -> Dict:
    context = {}
    context["esi_job"] = esi_job.dict()
    return context
