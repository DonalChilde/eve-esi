import logging
from datetime import datetime
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from eve_esi_jobs.helpers import combine_dictionaries

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class JobCallback(BaseModel):
    callback_id: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

    class Config:
        extra = "forbid"


class CallbackCollection(BaseModel):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []

    class Config:
        extra = "forbid"


class EsiJobResult(BaseModel):
    work_order_name: Optional[str] = None
    work_order_id: Optional[str] = None
    data: Optional[Any] = None
    response: Optional[Any] = None

    class Config:
        extra = "forbid"


class EsiJob(BaseModel):
    id_: str = ""
    uid: UUID = Field(default_factory=uuid4)
    name: Optional[str]
    op_id: str
    retry_limit: int = 5
    parameters: Dict[str, Any] = {}
    result_callbacks: CallbackCollection = CallbackCollection()
    template_overrides: Dict[str, Any] = {}
    result: Optional[EsiJobResult] = None

    class Config:
        extra = "forbid"

    def callback_iter(self) -> Iterable:
        """An iterator that chains all the callbacks"""
        return chain(
            self.result_callbacks.success,
            self.result_callbacks.retry,
            self.result_callbacks.fail,
        )

    def add_template_overrides(self, override: Dict):
        """Update esi_job.template_over_rides with additional values"""
        self.template_overrides.update(override)

    def get_template_overrides(self):
        """return a new combined dict of esi_job parameters, and template_overrides.

        Overrides will overwrite local parameters.
        """
        params = combine_dictionaries(
            self.parameters, [self._build_parameters(), self.template_overrides]
        )

        return params

    def _build_parameters(self):
        """make a dict of all the esi_job parameters usable in templates"""
        params = {
            "esi_job_name": self.name,
            "esi_job_id": self.id_,
            "esi_job_op_id": self.op_id,
            "esi_job_retry_limit": self.retry_limit,
            "esi_job_uid": str(self.uid),
            "esi_job_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params


class EsiWorkOrder(BaseModel):
    id_: str = ""
    name: str = ""
    uid: UUID = Field(default_factory=uuid4)
    description: str = ""
    jobs: List[EsiJob] = []
    parent_path_template: str = ""
    template_overrides: Dict[str, Any] = {}

    class Config:
        extra = "forbid"

    def add_template_overrides(self, override: Dict):
        """Update EsiWorkOrder template_overrides with additional values"""
        self.template_overrides.update(override)

    def get_template_overrides(self):
        """return a new combined dict of EsiWorkOrder parameters and and template_overrides.

        template_overrides will overwrite parameters.
        """
        params = self._build_parameters()
        params.update(self.template_overrides)
        return params

    def _build_parameters(self):
        """make a dict of all the EsiWorkOrder parameters usable in templates"""
        params = {
            "ewo_name": self.name,
            "ewo_id": self.id_,
            "ewo_parent_path_template": self.parent_path_template,
            "ewo_uid": str(self.uid),
            "ewo_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params
