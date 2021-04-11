import logging
from datetime import datetime
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Union
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
    work_order_uid: str = ""
    data: Optional[Any] = None
    response: Optional[Any] = None
    attempts: int = 0

    class Config:
        extra = "forbid"


class EsiJob(BaseModel):
    id_: str = ""
    uid: UUID = Field(default_factory=uuid4)
    name: str = ""
    op_id: str
    retry_limit: int = 5
    parameters: Dict[str, Any] = {}
    callbacks: CallbackCollection = CallbackCollection()
    additional_attributes: Dict[str, Any] = {}
    result: Optional[EsiJobResult] = None

    class Config:
        extra = "forbid"

    def callback_iter(self) -> Iterable:
        """An iterator that chains all the callbacks"""
        return chain(
            self.callbacks.success,
            self.callbacks.retry,
            self.callbacks.fail,
        )

    def update_attributes(self, override: Dict):
        """Update esi_job.additional_attributes with additional values"""
        self.additional_attributes.update(override)

    def attributes(self):
        """return a new combined dict of esi_job attributes, and additional_attributes.

        additional_attributes will overwrite local attributes in new dict.
        """
        params = combine_dictionaries(
            self.parameters, [self._job_attributes(), self.additional_attributes]
        )

        return params

    def _job_attributes(self) -> Dict[str, Union[int, str, None]]:
        """make a dict of all the esi_job attributes usable in templates"""
        params: Dict[str, Union[int, str, None]] = {
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
    additional_attributes: Dict[str, Any] = {}

    class Config:
        extra = "forbid"

    def update_attributes(self, override: Dict):
        """Update EsiWorkOrder additional_attributes with additional values"""
        self.additional_attributes.update(override)

    def attributes(self):
        """return a new combined dict of EsiWorkOrder attributes and and additional_attributes.

        additional_attributes will overwrite local attributes in new dict.
        """
        params = self._ewo_atributes()
        params.update(self.additional_attributes)
        return params

    def _ewo_atributes(self) -> Dict[str, Union[int, str, None]]:
        """make a dict of all the EsiWorkOrder attributes usable in templates"""
        params: Dict[str, Union[int, str, None]] = {
            "ewo_name": self.name,
            "ewo_id": self.id_,
            "ewo_parent_path_template": self.parent_path_template,
            "ewo_uid": str(self.uid),
            "ewo_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params
