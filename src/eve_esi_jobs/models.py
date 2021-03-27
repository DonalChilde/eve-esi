from itertools import chain
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.collection_util import combine_dictionaries

# from rich import inspect


class JobCallback(BaseModel):
    callback_id: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    config: Optional[Dict[str, Any]]


class CallbackCollection(BaseModel):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []


class EsiJobResult(BaseModel):
    work_order_name: Optional[str] = None
    work_order_id: Optional[str] = None
    data: Optional[Any] = None
    response: Optional[Any] = None


class EsiJob(BaseModel):
    id_: Optional[str]
    name: Optional[str]
    op_id: str
    retry_limit: int = 5
    parameters: Dict[str, Any] = {}
    result_callbacks: CallbackCollection = CallbackCollection()
    over_rides: Dict[str, Any] = {}
    result: Optional[EsiJobResult] = None

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
        }
        return params


class EsiWorkOrder(BaseModel):
    id_: Optional[str]
    name: str = ""
    description: str = ""
    jobs: List[EsiJob] = []
    parent_path_template: str = ""
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
