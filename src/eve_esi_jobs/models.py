from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type

from pydantic import BaseModel

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.callbacks import SaveResultToFile
from eve_esi_jobs.model_helpers import combine_dictionaries
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpActionCallback,
    ResponseToJson,
    ResponseToText,
)

# from rich import inspect


@dataclass
class CallbackManifestEntry:
    callback: Type[AiohttpActionCallback]
    valid_targets: List[str] = field(default_factory=list)


CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
    "save_json_to_file": CallbackManifestEntry(
        callback=SaveResultToFile, valid_targets=["success"]
    ),
    "response_to_json": CallbackManifestEntry(
        callback=ResponseToJson, valid_targets=["success"]
    ),
    "response_to_text": CallbackManifestEntry(
        callback=ResponseToText, valid_targets=["success"]
    ),
}


class JobCallback(BaseModel):
    callback_id: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    config: Optional[Dict[str, Any]]


class CallbackCollection(BaseModel):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []


class EsiJob(BaseModel):
    id_: Optional[str]
    name: Optional[str]
    op_id: str
    retry_limit: int
    parameters: Dict[str, Any] = {}
    result_callbacks: CallbackCollection
    over_rides: Dict[str, Any] = {}

    def callback_iter(self) -> Iterable:
        return chain(
            self.result_callbacks.success,
            self.result_callbacks.retry,
            self.result_callbacks.fail,
        )

    def add_param_overrides(self, override: Dict):
        """Update esi_job param overrides with additional values"""
        self.over_rides.update(override)

    def get_params(self):
        """return a new combined dict of parameters, esi_job params, and overrides.

        Overrides will overwrite params.
        """
        params = combine_dictionaries(
            self.parameters, [self._build_parameters(), self.over_rides]
        )

        return params

    def _build_parameters(self):
        """make a dict of all the esi_job params usable in templates"""
        params = {
            "esi_job_name": self.name,
            "esi_job_id": self.id_,
            # "ewo_parent_path_template": self.parent_path_template,
        }
        return params


class EsiWorkOrder(BaseModel):
    id_: Optional[str]
    name: str
    jobs: List[EsiJob]
    parent_path_template: str
    over_rides: Dict[str, Any] = {}

    def add_param_overrides(self, override: Dict):
        """Update ewo param overrides with additional values"""
        self.over_rides.update(override)

    def get_params(self):
        """return a new combined dict of ewo params and overrides.

        Overrides will overwrite params.
        """
        params = self._build_parameters()
        params.update(self.over_rides)
        return params

    def _build_parameters(self):
        """make a dict of all the ewo params usable in templates"""
        params = {
            "ewo_name": self.name,
            "ewo_id": self.id_,
            "ewo_parent_path_template": self.parent_path_template,
        }
        return params


def deserialize_json_job(esi_job_json: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_json)
    return esi_job


def deserialize_json_work_order(esi_work_order_json: Dict) -> EsiWorkOrder:
    esi_work_order = EsiWorkOrder(**esi_work_order_json)
    return esi_work_order
