"""foo"""
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction, AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    LogFail,
    LogRetry,
    LogSuccess,
    ResponseContentToJson,
    SaveJsonResultToFile,
    SaveResultToFile,
)
from rich import inspect

from eve_esi_jobs.helpers import combine_dictionaries

# from eve_esi_jobs.eve_esi_jobs import serialize_job
from eve_esi_jobs.models import EsiJob, EsiJobResult

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
# TODO callback to generate market history summary

DEFAULT_CALLBACKS: ActionCallbacks = ActionCallbacks(
    success=[ResponseContentToJson(), LogSuccess()],
    retry=[LogRetry()],
    fail=[LogFail()],
)


# class SaveResultToCSVFile(AiohttpActionCallback):
#     """Save the result to a CSV file.

#     Expects the result to be a List[Dict].
#     """

#     # FIXME move this to Aiohttp-Queue
#     def __init__(
#         self,
#         file_path: str,
#         mode: str = "w",
#         field_names: Optional[List[str]] = None,
#         additional_fields: Dict = None,
#     ) -> None:
#         super().__init__()
#         self.file_path = Path(file_path)
#         self.mode = mode
#         self.field_names = field_names
#         self.additional_fields = additional_fields

#     def refine_path(self, caller: AiohttpAction, *args, **kwargs):
#         """Refine the file path. Data from the AiohttpAction is available for use here."""
#         # pass

#     def get_data(self, caller: AiohttpAction, *args, **kwargs) -> List[Dict]:
#         """expects caller.result to be a List[Dict]."""
#         _ = args
#         _ = kwargs
#         data = caller.result
#         if self.additional_fields is not None:
#             combined_data = []
#             for item in data:
#                 combined_data.append(
#                     combine_dictionaries(item, [self.additional_fields])
#                 )
#             return combined_data
#         return data

#     async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
#         self.refine_path(caller, *args, **kwargs)
#         try:
#             self.file_path.parent.mkdir(parents=True, exist_ok=True)
#             data = self.get_data(caller, args, kwargs)
#             if self.field_names is None:
#                 self.field_names = list(data[0].keys())
#             with open(str(self.file_path), mode=self.mode) as file:
#                 writer = csv.DictWriter(file, fieldnames=self.field_names)
#                 writer.writeheader()
#                 for item in data:
#                     writer.writerow(item)
#         except Exception as ex:
#             logger.exception(
#                 "Exception saving file to %s in action %s", self.file_path, caller
#             )
#             raise ex


# class SaveCsvResultToFile(SaveJsonResultToFile):
#     def __init__(self, file_path: str, mode: str) -> None:
#         super().__init__(file_path, mode=mode)
class SaveEsiJobToJsonFile(SaveResultToFile):
    """Save an `EsiJob` to file after execution.

    Previous callbacks decide if the `EsiJob` contains the result data,
    and/or the response data"""

    def __init__(
        self,
        file_path: str,
        mode: str = "w",
        path_values: Optional[Dict[str, str]] = None,
        file_ending: str = ".json",
    ) -> None:
        super().__init__(
            file_path,
            mode=mode,
            path_values=path_values,
            file_ending=file_ending,
        )

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects data (caller.result in super) to be json."""
        job: EsiJob = caller.context.get("esi_job", None)
        if job is not None:
            data_string = job.json(indent=2)
        else:
            data_string = ""
        # logger.info("response meta: %s", caller.response_meta_to_json())
        # if data is None or not data:
        #     logger.warning(
        #         "Could not get result data from esi_job. job: %s action: %s",
        #         job,
        #         caller,
        #     )
        #     data = {}
        # inspect(data)
        # json_string = json.dumps(data, indent=2)
        return data_string


class ResultToEsiJob(AiohttpActionCallback):
    """Copies result to `EsiJob` for use outside of event loop"""

    def __init__(self) -> None:
        super().__init__()

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: "EsiJob" = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        if esi_job.result is None:
            esi_job.result = EsiJobResult()
        esi_job.result.data = caller.result
        job_attributes = esi_job.attributes()
        esi_job.result.work_order_id = job_attributes.get("ewo_id", "")  # type: ignore
        esi_job.result.work_order_name = job_attributes.get("ewo_name", "")  # type: ignore
        esi_job.result.work_order_uid = job_attributes.get("ewo_uid", "")


class ResponseToEsiJob(AiohttpActionCallback):
    """Copies response info to the `EsiJob` in json format."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: EsiJob = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        # if caller.response is not None:
        #     esi_job.result["response"] = response_to_json(caller.response)
        if esi_job.result is None:
            esi_job.result = EsiJobResult()
        esi_job.result.response = caller.response_meta_to_json()
        job_attributes = esi_job.attributes()
        print(job_attributes)
        esi_job.result.work_order_id = job_attributes.get("ewo_id", "")
        esi_job.result.work_order_name = job_attributes.get("ewo_name", "")
        esi_job.result.work_order_uid = job_attributes.get("ewo_uid", "")


class LogJobFailure(AiohttpActionCallback):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        try:
            esi_job: EsiJob = caller.context.get("esi_job", None)
            job_string = esi_job.json(indent=2)
            logger.warning("Job failed. %s", job_string)
        except Exception as ex:
            logger.exception("failure in callback %s", ex)
