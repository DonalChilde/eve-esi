import json
import logging
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from eve_esi_jobs.helpers import combine_dictionaries

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class SerializeMixin:
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
        # cls = self.__class__
        return cls(**obj)

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
    callback_id: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

    class Config:
        extra = "forbid"


class CallbackCollection(BaseModel, SerializeMixin):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []

    class Config:
        extra = "forbid"


class EsiJobResult(BaseModel, SerializeMixin):
    work_order_name: Optional[str] = None
    work_order_id: Optional[str] = None
    work_order_uid: str = ""
    attempts: int = 0
    response: Optional[Any] = None
    data: Optional[Any] = None

    class Config:
        extra = "forbid"


class EsiJob(BaseModel, SerializeMixin):
    name: str = ""
    description: str = ""
    id_: str = ""
    uid: UUID = Field(default_factory=uuid4)
    op_id: str
    max_attempts: int = 5
    parameters: Dict[str, Any] = {}
    additional_attributes: Dict[str, Any] = {}
    callbacks: CallbackCollection = CallbackCollection()
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
            "esi_job_id_": self.id_,
            "esi_job_op_id": self.op_id,
            "esi_job_max_attempts": self.max_attempts,
            "esi_job_uid": str(self.uid),
            "esi_job_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params


class EsiWorkOrder(BaseModel, SerializeMixin):
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
            "ewo_output_path": self.output_path,
            "ewo_uid": str(self.uid),
            "ewo_iso_date_time": datetime.now().isoformat().replace(":", "-"),
        }
        return params
