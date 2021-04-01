"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type

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
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import EsiJob, JobCallback

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
    kwargs = update_template_params(kwargs, template_overrides)
    callback = SaveJsonResultToFile(*args, **kwargs)
    return callback


def build_save_list_of_dict_result_to_csv_file(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> SaveListOfDictResultToCSVFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_template_params(kwargs, template_overrides)
    callback = SaveListOfDictResultToCSVFile(*args, **kwargs)
    return callback


def build_save_esi_job_to_json_file(
    job_callback: JobCallback, template_overrides: Optional[Dict] = None
) -> SaveEsiJobToJsonFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_template_params(kwargs, template_overrides)
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


CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
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


def update_template_params(kwargs, template_overrides: Optional[Dict] = None):
    template_params = kwargs.get("template_params", {})
    template_overrides = optional_object(template_overrides, dict)
    callback_template_overrides = combine_dictionaries(
        template_params, [template_overrides]
    )
    kwargs["template_params"] = callback_template_overrides
    return kwargs
