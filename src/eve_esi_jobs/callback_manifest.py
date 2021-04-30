"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type

from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    CheckForPages,
    ResponseContentToJson,
    ResponseContentToText,
    SaveListOfDictResultToCSVFile,
    SaveResultToJsonFile,
    SaveResultToYamlFile,
)

from eve_esi_jobs.callbacks import (
    LogJobFailure,
    ResponseToEsiJob,
    ResultToEsiJob,
    SaveEsiJobToJsonFile,
)
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import CallbackCollection, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CallbackManifestEntry:
    callback: Type[AiohttpActionCallback]
    factory_function: Callable
    valid_targets: List[str] = field(default_factory=list)


def build_save_result_to_json_file(
    job_callback: JobCallback, **kwargs
) -> SaveResultToJsonFile:
    _ = kwargs
    callback = SaveResultToJsonFile(*job_callback.args, **job_callback.kwargs)
    return callback


def build_save_list_of_dict_result_to_csv_file(
    job_callback: JobCallback, **kwargs
) -> SaveListOfDictResultToCSVFile:
    _ = kwargs
    callback = SaveListOfDictResultToCSVFile(*job_callback.args, **job_callback.kwargs)
    return callback


def build_save_result_to_yaml_file(
    job_callback: JobCallback, **kwargs
) -> SaveResultToYamlFile:
    _ = kwargs
    callback = SaveResultToYamlFile(*job_callback.args, **job_callback.kwargs)
    return callback


def build_save_esi_job_to_json_file(
    job_callback: JobCallback, **kwargs
) -> SaveEsiJobToJsonFile:
    _ = kwargs
    # job_callback.kwargs["file_path_template"] = Path(
    #     job_callback.kwargs["file_path_template"]
    # )
    callback = SaveEsiJobToJsonFile(*job_callback.args, **job_callback.kwargs)
    return callback


def build_result_to_esi_job(job_callback: JobCallback, **kwargs) -> ResultToEsiJob:
    _, _ = job_callback, kwargs
    return ResultToEsiJob()


def build_response_to_esi_job(job_callback: JobCallback, **kwargs) -> ResponseToEsiJob:
    _, _ = job_callback, kwargs
    return ResponseToEsiJob()


def build_response_content_to_json(
    job_callback: JobCallback, **kwargs
) -> ResponseContentToJson:
    _, _ = job_callback, kwargs
    return ResponseContentToJson()


def build_response_content_to_text(
    job_callback: JobCallback, **kwargs
) -> ResponseContentToText:
    _, _ = job_callback, kwargs
    return ResponseContentToText()


def build_check_for_pages(job_callback: JobCallback, **kwargs) -> CheckForPages:
    _, _ = job_callback, kwargs
    return CheckForPages()


def build_log_job_failure(job_callback: JobCallback, **kwargs) -> LogJobFailure:
    _, _ = job_callback, kwargs
    return LogJobFailure()


class CallbackManifest:
    def __init__(
        self, manifest_entries: Optional[Dict[str, CallbackManifestEntry]] = None
    ) -> None:
        self.manifest_entries: Dict[str, CallbackManifestEntry] = optional_object(
            manifest_entries, dict
        )

    @staticmethod
    def manifest_factory():
        return new_manifest()

    def add_callback(
        self,
        callback_id: str,
        callback: Type[ActionCallbacks],
        factory_function: Callable,
        valid_targets: List[str],
    ):
        self.manifest_entries[callback_id] = CallbackManifestEntry(
            callback=callback,
            factory_function=factory_function,
            valid_targets=valid_targets,
        )

    def init_callback(self, target: str, job_callback: JobCallback, **kwargs):
        entry = self.manifest_entries.get(job_callback.callback_id, None)
        if entry is None:
            raise ValueError(
                f"{job_callback.callback_id} is not a registered callback."
            )
        if target not in entry.valid_targets:
            raise ValueError(
                (
                    f"Invalid target for {job_callback.callback_id}. Tried {target}, "
                    f"expected one of {entry.valid_targets}"
                )
            )
        try:
            callback = entry.factory_function(job_callback, **kwargs)
        except Exception as ex:
            logger.exception(
                "Failed to initialize callback with %s. Did you supply the correct arguments?",
                job_callback.callback_id,
            )
            # incorrect kwargs to call back
            raise ex
        return callback

    def build_action_callbacks(
        self,
        job_callbacks: CallbackCollection,
    ) -> ActionCallbacks:
        action_callbacks = ActionCallbacks()
        for job_callback in job_callbacks.success:
            action_callback = self.init_callback("success", job_callback)
            action_callbacks.success.append(action_callback)
        for job_callback in job_callbacks.retry:
            action_callback = self.init_callback("retry", job_callback)
            action_callbacks.retry.append(action_callback)
        for job_callback in job_callbacks.fail:
            action_callback = self.init_callback("fail", job_callback)
            action_callbacks.fail.append(action_callback)
        return action_callbacks


def new_manifest():
    manifest_entries: Dict[str, CallbackManifestEntry] = {
        "log_job_failure": CallbackManifestEntry(
            callback=LogJobFailure,
            valid_targets=["fail"],
            factory_function=build_log_job_failure,
        ),
        "check_for_pages": CallbackManifestEntry(
            callback=CheckForPages,
            valid_targets=["success"],
            factory_function=build_check_for_pages,
        ),
        "save_result_to_json_file": CallbackManifestEntry(
            callback=SaveResultToJsonFile,
            valid_targets=["success"],
            factory_function=build_save_result_to_json_file,
        ),
        "save_result_to_yaml_file": CallbackManifestEntry(
            callback=SaveResultToYamlFile,
            valid_targets=["success"],
            factory_function=build_save_result_to_yaml_file,
        ),
        "save_list_of_dict_result_to_csv_file": CallbackManifestEntry(
            callback=SaveListOfDictResultToCSVFile,
            valid_targets=["success"],
            factory_function=build_save_list_of_dict_result_to_csv_file,
        ),
        "save_esi_job_to_json_file": CallbackManifestEntry(
            callback=SaveEsiJobToJsonFile,
            valid_targets=["success", "fail"],
            factory_function=build_save_esi_job_to_json_file,
        ),
        "result_to_esi_job": CallbackManifestEntry(
            callback=ResultToEsiJob,
            valid_targets=["success"],
            factory_function=build_result_to_esi_job,
        ),
        "response_to_esi_job": CallbackManifestEntry(
            callback=ResponseToEsiJob,
            valid_targets=["success", "fail"],
            factory_function=build_response_to_esi_job,
        ),
        "response_content_to_json": CallbackManifestEntry(
            callback=ResponseContentToJson,
            valid_targets=["success"],
            factory_function=build_response_content_to_json,
        ),
        "response_content_to_text": CallbackManifestEntry(
            callback=ResponseContentToText,
            valid_targets=["success"],
            factory_function=build_response_content_to_text,
        ),
    }
    manifest = CallbackManifest(manifest_entries=manifest_entries)
    return manifest
