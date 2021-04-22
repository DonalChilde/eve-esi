import logging
from typing import Any, Dict, List, Optional, Sequence

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction
from pfmsoft.aiohttp_queue.aiohttp import ActionObserver

from eve_esi_jobs.callback_manifest import CallbackManifest
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import EsiJob

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def validate_job(esi_job: EsiJob, esi_provider: EsiProvider):
    _, _ = esi_job, esi_provider
    raise NotImplementedError()
    # raise error if fail
    # validate esi params
    # instance callbacks to check valid args? build_action_callbacks


class JobsToActions:
    """Contains logic for turning a :class:`EsiJob` into an :class:`~pfmsoft.aiohttp_queue.aiohttp.AiohttpAction`"""

    def __init__(self) -> None:
        pass

    def make_actions(
        self,
        esi_jobs: Sequence[EsiJob],
        esi_provider: EsiProvider,
        callback_manifest: CallbackManifest,
        observers: Optional[List[ActionObserver]] = None,
    ) -> List[AiohttpAction]:
        """
        Translate :class:`EsiJob` s into :class:`~pfmsoft.aiohttp_queue.aiohttp.AiohttpAction` s

        Args:
            esi_jobs: The jobs to get actions from.
            esi_provider: The esi_provider.
            callback_manifest: the callback manifest used to init the
                :class:`~pfmsoft.aiohttp_queue.aiohttp.AiohttpActionCallback` s
            observers: Observers for the actions. Defaults to None.

        """
        actions = []
        observers = optional_object(observers, list)
        for esi_job in esi_jobs:
            action = esi_provider.build_action_from_op_id(
                op_id=esi_job.op_id,
                path_params=self._build_path_params(esi_job, esi_provider),
                query_params=self._build_query_params(esi_job, esi_provider),
                callbacks=self._build_action_callbacks(esi_job, callback_manifest),
                max_attempts=esi_job.max_attempts,
                request_kwargs=self._build_request_kwargs(esi_job, esi_provider),
                context=self._build_context(esi_job, esi_provider),
            )
            action.observers.extend(observers)
            actions.append(action)
        return actions

    def _build_path_params(self, esi_job, esi_provider) -> Dict[str, Any]:
        """
        Return the path parameters.
        """
        try:
            path_params = self._split_parameters(esi_job, "path", esi_provider)
            return path_params
        except ValueError as ex:
            logger.warning("Missing required parameter %s", ex)
            raise ex

    def _split_parameters(
        self, esi_job: EsiJob, split_id: str, esi_provider: EsiProvider
    ) -> Dict:
        """
        Finds all the EsiJob.parameters that have a location matching split_id,
        check for missing params.
        """
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
            logger.warning("Missing required parameter %s in %r", ex, action_json)
            raise ex
        return path_params

    def _build_action_callbacks(
        self,
        esi_job: EsiJob,
        callback_manifest: CallbackManifest,
    ) -> ActionCallbacks:
        action_callbacks = ActionCallbacks()
        for job_callback in esi_job.callbacks.success:
            action_callback = callback_manifest.init_callback("success", job_callback)
            action_callbacks.success.append(action_callback)
        for job_callback in esi_job.callbacks.retry:
            action_callback = callback_manifest.init_callback("retry", job_callback)
            action_callbacks.retry.append(action_callback)
        for job_callback in esi_job.callbacks.fail:
            action_callback = callback_manifest.init_callback("fail", job_callback)
            action_callbacks.fail.append(action_callback)
        return action_callbacks

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
        #   params - used to build the query string
        #   data/json - sent in the body of the request
        #   headers
        #   auth? expect to use oauth token

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
            raise ValueError(f"could not find opid {esi_job.op_id}")
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
