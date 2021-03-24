from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type

from pydantic import BaseModel
from rich import inspect

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.jobs.callbacks import SaveResultToFile
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
    ResponseToJson,
    ResponseToText,
)


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


class CallbackCollection(BaseModel):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []


class EsiJob(BaseModel):
    op_id: str
    retry_limit: int
    parameters: Dict[str, Any] = {}
    result_callbacks: CallbackCollection


esi_job_json_format = {
    "op_id": "value",
    "retry_limit": 1,
    "parameters": {},
    "result_callbacks": {
        "success": [
            {
                "callback_id": "id of callback",
                "args": "list of arguments to callback",
                "kwargs": {"key1": "value"},
            }
        ],
        "fail": [],
        "retry": [],
    },
}


def deserialize_json_job(esi_job_json: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_json)
    return esi_job
