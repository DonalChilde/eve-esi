"""A lookup table of valid callbacks for Esi Jobs."""
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type

from eve_esi_jobs.callbacks import (
    EsiJobCallback,
    SaveEsiJobToJsonFile,
    SaveEsiJobToYamlFile,
    SaveJobResultToJsonFile,
    SaveJobResultToYamlFile,
    SaveListOfDictResultToCSVFile,
)
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import EsiJob, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CallbackManifestEntry:
    callback: Type[EsiJobCallback]
    factory_function: Callable


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
        callback: Type[EsiJobCallback],
        factory_function: Callable,
    ):
        self.manifest_entries[callback_id] = CallbackManifestEntry(
            callback=callback,
            factory_function=factory_function,
        )

    def init_callback(self, job_callback: JobCallback, job: EsiJob) -> EsiJobCallback:
        entry = self.manifest_entries.get(job_callback.callback_id, None)
        if entry is None:
            raise ValueError(
                f"{job_callback.callback_id} is not a registered callback."
            )

        try:
            callback = entry.factory_function(job=job, **job_callback.kwargs)
        except Exception as ex:
            logger.exception(
                "Failed to initialize callback with %s. Did you supply the correct arguments?",
                job_callback.callback_id,
            )
            # incorrect kwargs to call back
            raise ex
        return callback


def new_manifest():
    manifest_entries: Dict[str, CallbackManifestEntry] = {
        "save_result_to_json_file": CallbackManifestEntry(
            callback=SaveJobResultToJsonFile,
            factory_function=SaveJobResultToJsonFile,
        ),
        "save_result_to_yaml_file": CallbackManifestEntry(
            callback=SaveJobResultToYamlFile,
            factory_function=SaveJobResultToYamlFile,
        ),
        "save_list_of_dict_result_to_csv_file": CallbackManifestEntry(
            callback=SaveListOfDictResultToCSVFile,
            factory_function=SaveListOfDictResultToCSVFile,
        ),
        "save_esi_job_to_json_file": CallbackManifestEntry(
            callback=SaveEsiJobToJsonFile,
            factory_function=SaveEsiJobToJsonFile,
        ),
        "save_esi_job_to_yaml_file": CallbackManifestEntry(
            callback=SaveEsiJobToYamlFile,
            factory_function=SaveEsiJobToYamlFile,
        ),
    }
    manifest = CallbackManifest(manifest_entries=manifest_entries)
    return manifest
