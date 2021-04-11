import logging
from typing import Any, Dict, List, Optional, Sequence

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction, AiohttpActionCallback

from eve_esi_jobs.callback_manifest import CallbackProvider
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import EsiJob, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def validate_job(esi_job: EsiJob, esi_provider: EsiProvider):
    _, _ = esi_job, esi_provider
    # raise error if fail
    # validate esi params
    # instance callbacks to check valid args? build_action_callbacks


class JobsToActions:
    def __init__(self) -> None:
        pass

    def make_actions(
        self,
        esi_jobs: Sequence[EsiJob],
        esi_provider: EsiProvider,
        callback_provider: CallbackProvider,
        additional_attributes: Optional[Dict[str, str]],
    ) -> List[AiohttpAction]:
        actions = []
        additional_attributes = optional_object(additional_attributes, dict)
        for esi_job in esi_jobs:
            action = esi_provider.build_action_from_op_id(
                op_id=esi_job.op_id,
                path_params=self._build_path_params(esi_job, esi_provider),
                query_params=self._build_query_params(esi_job, esi_provider),
                callbacks=self._build_action_callbacks(
                    esi_job, callback_provider, additional_attributes
                ),
                retry_limit=esi_job.retry_limit,
                request_kwargs=self._build_request_kwargs(esi_job, esi_provider),
                context=self._build_context(esi_job, esi_provider),
            )
            actions.append(action)
        return actions

    def _build_path_params(self, esi_job, esi_provider) -> Dict[str, Any]:
        try:
            path_params = self._split_parameters(esi_job, "path", esi_provider)
            return path_params
        except ValueError as ex:
            logger.warning("Missing required parameter %s", ex)
            # FIXME what to do about errors
            return {}

    def _split_parameters(
        self, esi_job: EsiJob, split_id: str, esi_provider: EsiProvider
    ) -> Dict:
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

    def _build_query_params(
        self, action_json: EsiJob, esi_provider: EsiProvider
    ) -> Dict:
        try:
            path_params = self._split_parameters(action_json, "query", esi_provider)
        except ValueError as ex:
            logger.warning("Missing required parameter %s", ex)
        return path_params

    def _build_action_callbacks(
        self,
        esi_job: EsiJob,
        callback_provider: CallbackProvider,
        additional_attributes: Dict,
    ) -> ActionCallbacks:
        action_callbacks = ActionCallbacks()
        combined_attributes = combine_dictionaries(
            esi_job.attributes(), [additional_attributes]
        )
        for job_callback in esi_job.callbacks.success:
            action_callback = callback_provider.configure_action_callback(
                "success", job_callback, combined_attributes
            )
            action_callbacks.success.append(action_callback)
        for job_callback in esi_job.callbacks.retry:
            action_callback = callback_provider.configure_action_callback(
                "retry", job_callback, combined_attributes
            )
            action_callbacks.retry.append(action_callback)
        for job_callback in esi_job.callbacks.fail:
            action_callback = callback_provider.configure_action_callback(
                "fail", job_callback, combined_attributes
            )
            action_callbacks.fail.append(action_callback)

        return action_callbacks

    # def _build_target_callbacks(
    #     self, target: str, job_callbacks: List[JobCallback], additional_attributes: Dict
    # ) -> List[AiohttpActionCallback]:
    #     # logger.info("additional_attributes %s", additional_attributes)
    #     callbacks: List[AiohttpActionCallback] = []
    #     for job_callback in job_callbacks:
    #         callback_id = job_callback.callback_id
    #         manifest_entry = CALLBACK_MANIFEST.get(callback_id, None)
    #         if manifest_entry is None:
    #             raise ValueError(
    #                 f"Unable to find {callback_id} in manifest. Is it a valid callback id?"
    #             )
    #         if target not in manifest_entry.valid_targets:
    #             raise ValueError(
    #                 (
    #                     f"Invalid target for {callback_id}. Tried {target}, "
    #                     "expected one of {manifest_entry.valid_targets}"
    #                 )
    #             )
    #         try:
    #             callback = manifest_entry.config_function(
    #                 job_callback=job_callback,
    #                 additional_attributes=additional_attributes,
    #             )

    #             callbacks.append(callback)
    #         except Exception as ex:
    #             logger.exception(
    #                 "Failed to initialize callback with %s. Did you supply the correct arguments?",
    #                 callback_id,
    #             )
    #             raise ex
    #     return callbacks

    def _build_headers(
        self, esi_job: EsiJob, esi_provider: EsiProvider
    ) -> Optional[Dict]:
        headers: Dict = {}
        _, _ = esi_job, esi_provider
        if not headers:
            return None
        return headers

    def _build_request_kwargs(
        self, esi_job: EsiJob, esi_provider: EsiProvider
    ) -> Dict[str, Any]:
        # request kwargs include:
        # params - used to build the query string
        # data/json - sent in the body of the request
        # headers
        # auth? expect to use oauth token

        request_kwargs: Dict[str, Any] = {}
        body_param = self._check_for_body_param(esi_job, esi_provider)
        if body_param is not None:
            json_data = esi_job.parameters.get(body_param, [])
            if json_data:
                request_kwargs["json"] = json_data
        request_kwargs["params"] = self._build_query_params(esi_job, esi_provider)
        request_kwargs["headers"] = self._build_headers(esi_job, esi_provider)
        return request_kwargs

    def _check_for_body_param(
        self, esi_job: EsiJob, esi_provider: EsiProvider
    ) -> Optional[str]:
        """Check to see if any of the schema params is a body param.

        get this so that body param can be added to request_kwargs.
        """
        body_keys = []
        op_info = esi_provider.op_id_lookup.get(esi_job.op_id, None)
        if op_info is None:
            raise ValueError("could not find opid %s", esi_job.op_id)
        for param in op_info.parameters.values():
            if param.get("in", "") == "body":
                body_keys.append(param["name"])
        if len(body_keys) > 1:
            logger.warning("found more than one body param in %s", op_info)
        if body_keys:
            return body_keys[0]
        return None

    def _build_context(self, esi_job: EsiJob, esi_provider: EsiProvider) -> Dict:
        _ = esi_provider
        context = {}
        context["esi_job"] = esi_job
        return context
