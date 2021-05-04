import logging
from string import Template
from typing import List, Optional

from pfmsoft.aiohttp_queue import AiohttpAction
from pfmsoft.aiohttp_queue.aiohttp import ActionObserver, AiohttpRequest

from eve_esi_jobs.callback_manifest import CallbackManifest, new_manifest
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import EsiJob
from eve_esi_jobs.operation_manifest import OperationManifest

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class JobsToActions:
    def __init__(self) -> None:
        pass

    def make_action(
        self,
        esi_job: EsiJob,
        operation_manifest: OperationManifest,
        callback_manifest: Optional[CallbackManifest] = None,
        observers: Optional[List[ActionObserver]] = None,
    ):
        callback_manifest = optional_object(callback_manifest, new_manifest)
        observers = optional_object(observers, list)
        op_info = operation_manifest.op_info(esi_job.op_id)
        op_info.check_params(esi_job.parameters)
        request_params = op_info.request_params_to_locations(esi_job.parameters)
        url_template = Template(operation_manifest.url_template(esi_job.op_id))
        context = {"esi_job": esi_job}
        aiohttp_args = AiohttpRequest(
            method=op_info.method,
            url=url_template.substitute(request_params.path),
            params=request_params.query,
            json=request_params.body,
            headers=request_params.header,
        )
        action = AiohttpAction(
            aiohttp_args=aiohttp_args,
            name=esi_job.name,
            id_=esi_job.id_,
            max_attempts=5,
            callbacks=callback_manifest.build_action_callbacks(esi_job.callbacks),
            context=context,
        )
        action.observers.extend(observers)
        return action

    def make_actions(
        self,
        esi_jobs: List[EsiJob],
        operation_manifest: OperationManifest,
        callback_manifest: Optional[CallbackManifest] = None,
        observers: Optional[List[ActionObserver]] = None,
    ):
        callback_manifest = optional_object(callback_manifest, CallbackManifest)
        observers = optional_object(observers, list)
        actions = []
        for esi_job in esi_jobs:
            action = self.make_action(
                esi_job,
                operation_manifest=operation_manifest,
                callback_manifest=callback_manifest,
                observers=observers,
            )
            actions.append(action)
        return actions
