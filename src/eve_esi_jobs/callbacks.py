"""foo"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import aiohttp
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction, AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import (
    LogFail,
    LogRetry,
    LogSuccess,
    ResponseContentToJson,
    SaveJsonResultToFile,
)
from rich import inspect

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.models import EsiJob, EsiJobResult

# TODO callback to generate market history summary

DEFAULT_CALLBACKS: ActionCallbacks = ActionCallbacks(
    success=[ResponseContentToJson(), LogSuccess()],
    retry=[LogRetry()],
    fail=[LogFail()],
)
# class SaveResultToFile(AiohttpActionCallback):
#     """Usually used after ResponseToText callback"""

#     def __init__(self, file_path: str, mode: str = "w") -> None:
#         super().__init__()
#         self.file_path = Path(file_path)
#         self.mode = mode

#     def refine_path(self, caller: AiohttpAction, *args, **kwargs):
#         """Refine the file path. Data from the AiohttpAction is available for use here."""
#         # noop

#     def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
#         """expects caller.result to be a string."""
#         data = caller.result
#         return data

#     async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
#         self.refine_path(caller, args, kwargs)
#         try:
#             self.file_path.parent.mkdir(parents=True, exist_ok=True)
#             async with aiofiles.open(
#                 str(self.file_path), mode=self.mode
#             ) as file:  # type:ignore
#                 # with open(self.file_path, mode=self.mode) as file:
#                 data = self.get_data(caller, args, kwargs)
#                 await file.write(data)
#         except Exception as ex:
#             logger.exception("Exception saving file to %s", self.file_path)


# class SaveJsonResultToFile(SaveResultToFile):
#     """Usually used after ResponseToJson callback."""

#     def __init__(self, file_path: str, mode: str = "w") -> None:
#         super().__init__(file_path, mode=mode)

#     def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
#         """expects data (caller.result in super) to be json."""
#         data = super().get_data(caller, *args, **kwargs)
#         json_data = json.dumps(data, indent=2)
#         return json_data


class SaveEsiJobToJson(SaveJsonResultToFile):
    """data location can be either caller or job"""

    def __init__(
        self,
        file_path: str,
        mode: str = "w",
    ) -> None:
        super().__init__(file_path, mode=mode)

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects data (caller.result in super) to be json."""
        job: EsiJob = caller.context.get("esi_job", None)
        if job is not None:
            data = job.dict()
        if data is None or not data:
            logger.warning(
                "Could not get result data from esi_job. job: %s action: %s",
                job,
                caller,
            )
        # inspect(data)
        json_string = json.dumps(data, indent=2)
        return json_string


class ResultToEsiJob(AiohttpActionCallback):
    """Copies result to EsiJob for use outside of event loop"""

    def __init__(self) -> None:
        super().__init__()

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: "EsiJob" = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        if esi_job.result is None:
            esi_job.result = EsiJobResult()
        esi_job.result.data = caller.result
        esi_job.result.work_order_id = esi_job.get_params().get("ewo_id", "")  # type: ignore
        esi_job.result.work_order_name = esi_job.get_params().get("ewo_name", "")  # type: ignore


class ResponseToEsiJob(AiohttpActionCallback):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: "EsiJob" = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        # if caller.response is not None:
        #     esi_job.result["response"] = response_to_json(caller.response)
        if esi_job.result is None:
            esi_job.result = EsiJobResult()
        esi_job.result.response = response_to_json(caller.response)
        esi_job.result.work_order_id = esi_job.get_params().get("ewo_id", "")  # type: ignore
        esi_job.result.work_order_name = esi_job.get_params().get("ewo_name", "")  # type: ignore


def response_to_json(response: Optional[aiohttp.ClientResponse]) -> Dict:
    # TODO move this to AiohttpActions
    # TODO change name of Aiohttp callback from responsetojson to resulttojson
    # TODO make this a callback, figure out how to assign. attrgetter and a list of args?
    if response is not None:
        data: Dict[str, Any] = {}
        info = response.request_info
        request_headers = []
        for key, value in info.headers.items():
            request_headers.append({key: value})
        response_headers = [{key: value} for key, value in response.headers.items()]
        data["version"] = response.version
        data["status"] = response.status
        data["reason"] = response.reason
        data["method"] = info.method
        data["url"] = str(info.url)
        data["real_url"] = str(info.real_url)
        data["cookies"] = response.cookies
        data["request_headers"] = request_headers
        data["response_headers"] = response_headers
    else:
        data = {"error": "response to json called before response recieved."}
    return data
