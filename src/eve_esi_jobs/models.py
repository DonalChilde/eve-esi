import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from eve_esi_jobs.helpers import combine_dictionaries

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class SerializeMixin:
    """Provides serialization and deserialization functions for pydantic models."""

    def serialize_json(self, exclude_defaults=True, indent=2, **kwargs):
        serialized_json = self.json(
            exclude_defaults=exclude_defaults, indent=indent, **kwargs
        )
        return serialized_json

    def serialize_yaml(self):
        json_string = self.serialize_json()
        json_rep = json.loads(json_string)
        serialized_yaml = yaml.dump(json_rep, sort_keys=False)
        return serialized_yaml

    @classmethod
    def deserialize_obj(cls, obj: Dict):
        return cls(**obj)  # type: ignore

    @classmethod
    def deserialize_yaml(cls, yaml_string: str):
        obj = yaml.safe_load(yaml_string)
        instance = cls.deserialize_obj(obj)
        return instance

    @classmethod
    def deserialize_json(cls, json_string):
        obj = json.loads(json_string)
        instance = cls.deserialize_obj(obj)
        return instance

    @classmethod
    def deserialize_file(cls, file_path: Path):
        valid_suffixes = [".json", ".yaml"]
        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a file.")
        if file_path.suffix.lower() not in valid_suffixes:
            raise ValueError(f"Invalid file suffix, must be one of {valid_suffixes}")
        string_data = file_path.read_text()
        if file_path.suffix.lower() == ".json":
            return cls.deserialize_json(string_data)
        return cls.deserialize_yaml(string_data)

    def serialize_file(self, file_path: Path, file_format: str) -> Path:
        valid_formats = ["json", "yaml"]
        if file_format.lower() not in valid_formats:
            raise ValueError(f"Invalid file suffix, must be one of {valid_formats}")
        file_ending = "." + file_format
        if file_path.suffix.lower() != file_ending:
            file_path = file_path.with_suffix(file_ending)
        if file_format == "json":
            string_data = self.serialize_json()
        else:
            string_data = self.serialize_yaml()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(string_data)
        return file_path


class JobCallback(BaseModel, SerializeMixin):
    """
    A JobCallback contains the info necessary to create an instance of an actual
    callback at runtime.

    Args:
        callback_id (str): The id of the callback.
        args (List[Any]): A list of args used to init the callback
        kwargs (Dict[str, Any]): A dict used to init the callback
        config (Dict[str, Any]): A dict of values used in the factory function
            used to build the callback.
    """

    callback_id: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

    class Config:
        extra = "forbid"


# class CallbackCollection(BaseModel, SerializeMixin):
#     """
#     A collection of callbacks used by an :class:`EsiJob`

#     Args:
#         success (List[JobCallback]): Callbacks to be used for a successful request.
#         retry (List[JobCallback]): Callbacks to be used when a request is retried.
#         fail (List[JobCallback]): Callbacks to be used for a failed request.
#     """

#     success: List[JobCallback] = []
#     retry: List[JobCallback] = []
#     fail: List[JobCallback] = []

#     class Config:
#         extra = "forbid"


class EsiJobResult(BaseModel, SerializeMixin):
    r"""
    The result of an executed :class:`EsiJob`.

    Normally this class will be used by a callback to store response data on a job.
    If the correct callback is not used, this class will never be attatched to a job.

    The calbacks that currently create this class are:

    * :class:`~eve_esi_jobs.callbacks.ResponseToEsiJob`
    * :class:`~eve_esi_jobs.callbacks.ResultToEsiJob`

    Args:
        work_order_name (Optional[str]): The name of the containing workorder, if any.
        work_order_id (Optional[str]): The id\_ of the containing workorder, if any.
        work_order_uid (str): The uid of the containing workorder, if any.
        attempts (int): The number of attempts made.
        response (Optional[Any]): The data from :class:`Aiohttp.Response` as a dict.
            Only present if :class:`~eve_esi_jobs.callbacks.ResponseToEsiJob` was used.
        data (Optional[Any]): The data from a successful job. Only present if
            :class:`~eve_esi_jobs.callbacks.ResultToEsiJob` was used.
    """

    work_order_name: Optional[str] = None
    work_order_id: Optional[str] = None
    work_order_uid: str = ""
    attempts: int = 0
    response: Optional[Any] = None
    data: Optional[Any] = None

    class Config:
        extra = "forbid"


class EsiJob(BaseModel, SerializeMixin):
    """
    A job definining a request for the Eve Online ESI.

    Args:
        name (str): The name of the job.
        description (str): The description.
        id_ (str): The user-defined id.
        uid (UUID): A generated uuid4 unique identifier.
        op_id (str): The op_id of the job.
        max_attempts (int): The maximum number of attempts in the case of a retry.
            -1 means unlimited retrys. Default is 5.
        parameters (Dict[str, Any]): Parameters used by the request.
        additional_attributes (Dict[str, Any]): Additional attributes that can be used
            by callbacks.
        callbacks (CallbackCollection): Callbacks used by the job.
        result (Optional[EsiJobResult]): Information on the results of a job, only
            available when certain callbacks have been used. see :class:`EsiJobResult`
    """

    name: str = ""
    description: str = ""
    id_: str = ""
    uid: UUID = Field(default_factory=uuid4)
    op_id: str
    max_attempts: int = 5
    parameters: Dict[str, Any] = {}
    additional_attributes: Dict[str, Any] = {}
    callbacks: List[JobCallback] = []
    result: Optional[EsiJobResult] = None

    class Config:
        extra = "forbid"

    def update_attributes(self, override: Dict):
        """Update esi_job.additional_attributes with additional values"""
        self.additional_attributes.update(override)

    def attributes(self) -> Dict[str, str]:
        """Create a new dict with the combined values from :func:`EsiJob.parameters`,
        :func:`EsiJob.job_attributes`, and :class:`EsiJob.additional_attributes`.

        :class:`EsiJob.additional_attributes` will overwrite :func:`EsiJob.job_attributes`
        in the new dict.
        """
        params = combine_dictionaries(
            self.parameters, [self.job_attributes(), self.additional_attributes]
        )

        return params

    def job_attributes(self) -> Dict[str, str]:
        """Make a dict of all the esi_job attributes usable in templates

        Warning:
            Do not use this function directly to get attributes. Use :py:func:`EsiJob.attributes`
        """
        params: Dict[str, str] = {
            "esi_job_name": self.name,
            "esi_job_id_": self.id_,
            "esi_job_op_id": self.op_id,
            "esi_job_max_attempts": str(self.max_attempts),
            "esi_job_uid": str(self.uid),
            "esi_job_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params


class EsiWorkOrder(BaseModel, SerializeMixin):
    """
    A container class for :class:`EsiJob` s.

    Args:
        name (str): the name of the workorder.
        description (str): The description.
        id_ (str): The user-defined id.
        uid: (UUID) A generated uuid4 unique identifier.
        output_path (str): A path that will be prepended to any callback file paths for
            a workorder's jobs. May contain template values.
        additional_attributes (Dict[str, Any]): Additional attributes that can be
            used by job callbacks. Will override attributes generated by a workorder, or
            those of it's jobs.
        jobs (List[EsiJob]): The jobs
    """

    name: str = ""
    description: str = ""
    id_: str = ""
    uid: UUID = Field(default_factory=uuid4)
    output_path: str = ""
    additional_attributes: Dict[str, Any] = {}
    jobs: List[EsiJob] = []

    class Config:
        extra = "forbid"

    def update_attributes(self, override: Dict):
        """Update EsiWorkOrder additional_attributes with additional values"""
        self.additional_attributes.update(override)

    def attributes(self) -> Dict[str, str]:
        """Create a new dict with the combined values from :func:`EsiWorkOrder.ewo_attributes`,
        and :class:`EsiWorkOrder.additional_attributes`.

        :class:`EsiWorkOrder.additional_attributes` will overwrite values in
        :func:`EsiWorkOrder.ewo_attributes` in the new dict.
        """
        params = self.ewo_atributes()
        params.update(self.additional_attributes)
        return params

    def ewo_atributes(self) -> Dict[str, str]:
        """make a dict of all the EsiWorkOrder attributes usable in templates

        Warning:
            Do not use this function directly to get attributes. Use
            :py:func:`EsiWorkOrder.attributes`
        """
        params: Dict[str, str] = {
            "ewo_name": self.name,
            "ewo_id": self.id_,
            "ewo_output_path": self.output_path,
            "ewo_uid": str(self.uid),
            "ewo_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params
