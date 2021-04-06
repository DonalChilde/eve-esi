"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type

from pfmsoft.aiohttp_queue import AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    CheckForPages,
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
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CallbackManifestEntry:
    callback: Type[AiohttpActionCallback]
    config_function: Callable
    valid_targets: List[str] = field(default_factory=list)


def build_save_json_result_to_file(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> SaveJsonResultToFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_callback_path_values(kwargs, template_overrides)
    callback = SaveJsonResultToFile(*args, **kwargs)
    return callback


def build_save_list_of_dict_result_to_csv_file(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> SaveListOfDictResultToCSVFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_callback_path_values(kwargs, template_overrides)
    callback = SaveListOfDictResultToCSVFile(*args, **kwargs)
    return callback


def build_save_esi_job_to_json_file(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> SaveEsiJobToJsonFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_callback_path_values(kwargs, template_overrides)
    callback = SaveEsiJobToJsonFile(*args, **kwargs)
    return callback


def build_result_to_esi_job(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> ResultToEsiJob:
    _, _ = job_callback, template_overrides
    return ResultToEsiJob()


def build_response_to_esi_job(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> ResponseToEsiJob:
    _, _ = job_callback, template_overrides
    return ResponseToEsiJob()


def build_response_content_to_json(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> ResponseContentToJson:
    _, _ = job_callback, template_overrides
    return ResponseContentToJson()


def build_response_content_to_text(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> ResponseContentToText:
    _, _ = job_callback, template_overrides
    return ResponseContentToText()


def build_check_for_pages(
    job_callback, template_overrides: Optional[Dict] = None
) -> CheckForPages:
    _, _ = job_callback, template_overrides
    return CheckForPages()


CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
    "check_for_pages": CallbackManifestEntry(
        callback=CheckForPages,
        valid_targets=["success"],
        config_function=build_check_for_pages,
    ),
    "save_json_result_to_file": CallbackManifestEntry(
        callback=SaveJsonResultToFile,
        valid_targets=["success"],
        config_function=build_save_json_result_to_file,
    ),
    "save_list_of_dict_result_to_csv_file": CallbackManifestEntry(
        callback=SaveListOfDictResultToCSVFile,
        valid_targets=["success"],
        config_function=build_save_list_of_dict_result_to_csv_file,
    ),
    "save_esi_job_to_json_file": CallbackManifestEntry(
        callback=SaveEsiJobToJsonFile,
        valid_targets=["success", "fail"],
        config_function=build_save_esi_job_to_json_file,
    ),
    "result_to_esi_job": CallbackManifestEntry(
        callback=ResultToEsiJob,
        valid_targets=["success"],
        config_function=build_result_to_esi_job,
    ),
    "response_to_esi_job": CallbackManifestEntry(
        callback=ResponseToEsiJob,
        valid_targets=["success", "fail"],
        config_function=build_response_to_esi_job,
    ),
    "response_content_to_json": CallbackManifestEntry(
        callback=ResponseContentToJson,
        valid_targets=["success"],
        config_function=build_response_content_to_json,
    ),
    "response_content_to_text": CallbackManifestEntry(
        callback=ResponseContentToText,
        valid_targets=["success"],
        config_function=build_response_content_to_text,
    ),
}


def update_callback_path_values(kwargs, additional_values: Optional[Dict] = None):

    path_values = kwargs.get("path_values", {})
    additional_values = optional_object(additional_values, dict)
    updated_path_values = combine_dictionaries(path_values, [additional_values])
    kwargs["path_values"] = updated_path_values
    return kwargs
