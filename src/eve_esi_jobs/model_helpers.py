import logging
from pathlib import Path
from typing import Dict

from eve_esi_jobs.models import CallbackCollection, EsiJob, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class JobPreprocessor:
    def __init__(self) -> None:
        pass

    def pre_process_job(self, esi_job: EsiJob):
        job_attributes = esi_job.attributes()
        self._add_file_path_prefix_to_callbacks(esi_job, job_attributes)
        self._add_path_values_to_callbacks(esi_job, job_attributes)

    def _add_file_path_prefix_to_callbacks(self, esi_job: EsiJob, job_atributes: Dict):
        parent_path: str = job_atributes.get("ewo_output_path", "")
        for callback in esi_job.callback_iter():
            file_path = callback.kwargs.get("file_path", None)
            if file_path is not None:
                full_path_string = str(Path(parent_path) / Path(file_path))
                callback.kwargs["file_path"] = full_path_string

    def _add_path_values_to_callbacks(self, esi_job: EsiJob, job_attributes: Dict):
        for callback in esi_job.callback_iter():
            file_path = callback.kwargs.get("file_path", None)
            if file_path is not None:
                callback.kwargs["path_values"] = job_attributes


def default_callback_collection() -> CallbackCollection:
    callback_collection = CallbackCollection()
    callback_collection.success.append(
        JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.fail.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.fail.append(JobCallback(callback_id="log_job_failure"))
    return callback_collection
