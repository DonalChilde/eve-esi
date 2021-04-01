import logging
from typing import Any, Dict, List, Optional, Sequence

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction, AiohttpActionCallback
from rich import inspect

from eve_esi_jobs.callback_manifest import CALLBACK_MANIFEST
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import EsiJob, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
# FIXME default file name:${op_id}-${path parameters alpha sort?}-${isodate nanosecond}


def validate_job(esi_job: EsiJob, esi_provider: EsiProvider):
    _, _ = esi_job, esi_provider
    # raise error if fail
    # validate esi params
    # instance callbacks to check valid args? build_action_callbacks


def make_action_from_job(
    esi_job: EsiJob,
    esi_provider: EsiProvider,
    template_overrides: Optional[Dict] = None,
) -> AiohttpAction:
    template_overrides = optional_object(template_overrides, dict)
    action = esi_provider.build_action_from_op_id(
        op_id=esi_job.op_id,
        path_params=build_path_params(esi_job, esi_provider),
        query_params=build_query_params(esi_job, esi_provider),
        # callbacks=build_action_callbacks(esi_job, esi_provider),
        callbacks=build_action_callbacks(esi_job, template_overrides),
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
    # TODO refactor this to make more clear, add more validation?
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
    esi_job: EsiJob, template_overrides: Dict
) -> ActionCallbacks:
    callbacks: ActionCallbacks = ActionCallbacks()
    combined_overrides = combine_dictionaries(
        esi_job.get_template_overrides(), [template_overrides]
    )
    callbacks.success = build_target_callbacks(
        "success", esi_job.result_callbacks.success, combined_overrides
    )
    callbacks.retry = build_target_callbacks(
        "retry", esi_job.result_callbacks.retry, combined_overrides
    )
    callbacks.fail = build_target_callbacks(
        "fail", esi_job.result_callbacks.fail, combined_overrides
    )
    return callbacks


def build_target_callbacks(
    target: str, job_callbacks: List[JobCallback], template_overrides
) -> List[AiohttpActionCallback]:
    logger.info("template_overrides %s", template_overrides)
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
            callback = manifest_entry.config_function(
                job_callback,
                template_overrides=template_overrides,
            )

            callbacks.append(callback)
        except Exception as ex:
            logger.exception(
                "Failed to initialize callback with %s. Did you supply the correct arguments?",
                callback_id,
            )
            raise ex
    return callbacks


def build_headers(esi_job: EsiJob, esi_provider: EsiProvider) -> Optional[Dict]:
    headers: Dict = {}
    _, _ = esi_job, esi_provider
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
    request_kwargs["headers"] = build_headers(esi_job, esi_provider)
    return request_kwargs


def build_context(esi_job: EsiJob, esi_provider: EsiProvider) -> Dict:
    _ = esi_provider
    context = {}
    context["esi_job"] = esi_job
    return context
