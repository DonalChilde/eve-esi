"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    CheckForPages,
    ResponseContentToJson,
    ResponseContentToText,
    SaveJsonResultToFile,
    SaveListOfDictResultToCSVFile,
)

from eve_esi_jobs.callbacks import (
    LogJobFailure,
    ResponseToEsiJob,
    ResultToEsiJob,
    SaveEsiJobToJsonFile,
)
from eve_esi_jobs.helpers import combine_dictionaries, optional_object
from eve_esi_jobs.models import CallbackCollection, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CallbackManifestEntry:
    callback: Type[AiohttpActionCallback]
    config_function: Callable
    valid_targets: List[str] = field(default_factory=list)


def build_save_json_result_to_file(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> SaveJsonResultToFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_file_callback_path_values(kwargs, additional_attributes)
    callback = SaveJsonResultToFile(*args, **kwargs)
    return callback


def build_save_list_of_dict_result_to_csv_file(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> SaveListOfDictResultToCSVFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_file_callback_path_values(kwargs, additional_attributes)
    callback = SaveListOfDictResultToCSVFile(*args, **kwargs)
    return callback


def build_save_esi_job_to_json_file(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> SaveEsiJobToJsonFile:
    args = [*job_callback.args]
    kwargs = {**job_callback.kwargs}
    kwargs = update_file_callback_path_values(kwargs, additional_attributes)
    callback = SaveEsiJobToJsonFile(*args, **kwargs)
    return callback


def build_result_to_esi_job(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> ResultToEsiJob:
    _, _ = job_callback, additional_attributes
    return ResultToEsiJob()


def build_response_to_esi_job(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> ResponseToEsiJob:
    _, _ = job_callback, additional_attributes
    return ResponseToEsiJob()


def build_response_content_to_json(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> ResponseContentToJson:
    _, _ = job_callback, additional_attributes
    return ResponseContentToJson()


def build_response_content_to_text(
    job_callback: JobCallback, additional_attributes: Optional[Dict] = None
) -> ResponseContentToText:
    _, _ = job_callback, additional_attributes
    return ResponseContentToText()


def build_check_for_pages(
    job_callback, additional_attributes: Optional[Dict] = None
) -> CheckForPages:
    _, _ = job_callback, additional_attributes
    return CheckForPages()


def build_log_job_failure(
    job_callback, additional_attributes: Optional[Dict] = None
) -> LogJobFailure:
    _, _ = job_callback, additional_attributes
    return LogJobFailure()


# CALLBACK_MANIFEST: Dict[str, CallbackManifestEntry] = {
#     "log_job_failure": CallbackManifestEntry(
#         callback=LogJobFailure,
#         valid_targets=["fail"],
#         config_function=build_log_job_failure,
#     ),
#     "check_for_pages": CallbackManifestEntry(
#         callback=CheckForPages,
#         valid_targets=["success"],
#         config_function=build_check_for_pages,
#     ),
#     "save_json_result_to_file": CallbackManifestEntry(
#         callback=SaveJsonResultToFile,
#         valid_targets=["success"],
#         config_function=build_save_json_result_to_file,
#     ),
#     "save_list_of_dict_result_to_csv_file": CallbackManifestEntry(
#         callback=SaveListOfDictResultToCSVFile,
#         valid_targets=["success"],
#         config_function=build_save_list_of_dict_result_to_csv_file,
#     ),
#     "save_esi_job_to_json_file": CallbackManifestEntry(
#         callback=SaveEsiJobToJsonFile,
#         valid_targets=["success", "fail"],
#         config_function=build_save_esi_job_to_json_file,
#     ),
#     "result_to_esi_job": CallbackManifestEntry(
#         callback=ResultToEsiJob,
#         valid_targets=["success"],
#         config_function=build_result_to_esi_job,
#     ),
#     "response_to_esi_job": CallbackManifestEntry(
#         callback=ResponseToEsiJob,
#         valid_targets=["success", "fail"],
#         config_function=build_response_to_esi_job,
#     ),
#     "response_content_to_json": CallbackManifestEntry(
#         callback=ResponseContentToJson,
#         valid_targets=["success"],
#         config_function=build_response_content_to_json,
#     ),
#     "response_content_to_text": CallbackManifestEntry(
#         callback=ResponseContentToText,
#         valid_targets=["success"],
#         config_function=build_response_content_to_text,
#     ),
# }


def update_file_callback_path_values(kwargs, additional_values: Optional[Dict] = None):

    path_values = kwargs.get("path_values", {})
    additional_values = optional_object(additional_values, dict)
    updated_path_values = combine_dictionaries(path_values, [additional_values])
    kwargs["path_values"] = updated_path_values
    return kwargs


class DefaultCallbackFactory:
    def __init__(self) -> None:
        pass

    @staticmethod
    def default_callback_collection() -> CallbackCollection:
        callback_collection = CallbackCollection()
        callback_collection.success.append(
            JobCallback(callback_id="response_content_to_json")
        )
        callback_collection.success.append(
            JobCallback(callback_id="response_to_esi_job")
        )
        callback_collection.fail.append(JobCallback(callback_id="response_to_esi_job"))
        callback_collection.fail.append(JobCallback(callback_id="log_job_failure"))
        return callback_collection


class CallbackProvider:
    def __init__(self) -> None:
        self.callback_manifest = self._build_callback_manifest()

    def configure_action_callback(
        self, target: str, job_callback: JobCallback, additional_attributes: Dict
    ) -> AiohttpActionCallback:
        manifest_entry = self.callback_manifest.get(job_callback.callback_id, None)
        if manifest_entry is None:
            raise ValueError(
                f"Unable to find {job_callback.callback_id} in manifest. Is it a valid callback id?"
            )
        if target not in manifest_entry.valid_targets:
            raise ValueError(
                (
                    f"Invalid target for {job_callback.callback_id}. Tried {target}, "
                    "expected one of {manifest_entry.valid_targets}"
                )
            )
        try:
            callback = manifest_entry.config_function(
                job_callback=job_callback,
                additional_attributes=additional_attributes,
            )
            return callback
        except Exception as ex:
            logger.exception(
                "Failed to initialize callback with %s. Did you supply the correct arguments?",
                job_callback.callback_id,
            )
            # incorrect kwargs to call back
            raise ex

    def _build_callback_manifest(self) -> Dict[str, CallbackManifestEntry]:
        manifest: Dict[str, CallbackManifestEntry] = {
            "log_job_failure": CallbackManifestEntry(
                callback=LogJobFailure,
                valid_targets=["fail"],
                config_function=build_log_job_failure,
            ),
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
        return manifest
