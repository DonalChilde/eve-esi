from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type

from pydantic import BaseModel

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.callbacks import SaveResultToFile
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


class CallbackCollection(BaseModel):
    success: List[JobCallback] = []
    retry: List[JobCallback] = []
    fail: List[JobCallback] = []


class EsiJob(BaseModel):
    # job_id: str
    # name: str
    op_id: str
    retry_limit: int
    parameters: Dict[str, Any] = {}
    result_callbacks: CallbackCollection

    def callback_iter(self) -> Iterable:
        return chain(
            self.result_callbacks.success,
            self.result_callbacks.retry,
            self.result_callbacks.fail,
        )


class EsiWorkOrder(BaseModel):
    # work_order_id: str
    # work_order_name: str
    jobs: List[EsiJob]
    parent_path: Path
    over_ride: Dict[str, Any] = {}
