"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Type

from pfmsoft.aiohttp_queue import AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    ResponseContentToJson,
    ResponseContentToText,
    SaveJsonResultToFile,
    SaveListOfDictResultToCSVFile,
)

from eve_esi_jobs.callbacks import (
    ResponseToEsiJob,
    ResultToEsiJob,
    SaveEsiJobToJsonFile,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CallbackManifestEntry:
    callback: Type[AiohttpActionCallback]
    valid_targets: List[str] = field(default_factory=list)


CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
    "save_json_result_to_file": CallbackManifestEntry(
        callback=SaveJsonResultToFile, valid_targets=["success"]
    ),
    "save_list_of_dict_result_to_csv_file": CallbackManifestEntry(
        callback=SaveListOfDictResultToCSVFile, valid_targets=["success"]
    ),
    "save_esi_job_to_json_file": CallbackManifestEntry(
        callback=SaveEsiJobToJsonFile, valid_targets=["success", "fail"]
    ),
    "result_to_esi_job": CallbackManifestEntry(
        callback=ResultToEsiJob, valid_targets=["success"]
    ),
    "response_to_esi_job": CallbackManifestEntry(
        callback=ResponseToEsiJob, valid_targets=["success", "fail"]
    ),
    "response_content_to_json": CallbackManifestEntry(
        callback=ResponseContentToJson, valid_targets=["success"]
    ),
    "response_content_to_text": CallbackManifestEntry(
        callback=ResponseContentToText, valid_targets=["success"]
    ),
}
