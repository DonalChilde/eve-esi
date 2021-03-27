"""foo"""
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

import aiofiles
import aiohttp

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
)

if TYPE_CHECKING:
    from eve_esi_jobs.models import EsiJob


# TODO callback to generate market history summary


class SaveResultToFile(AiohttpActionCallback):
    """Usually used after ResponseToText callback"""

    def __init__(self, file_path: str, mode: str = "w") -> None:
        super().__init__()
        self.file_path = Path(file_path)
        self.mode = mode

    def refine_path(self, caller: AiohttpAction, *args, **kwargs):
        """Refine the file path. Data from the AiohttpAction is available for use here."""
        # noop

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects caller.result to be a string."""
        data = caller.result
        return data

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        self.refine_path(caller, args, kwargs)
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(str(self.file_path), mode=self.mode) as file:
                # with open(self.file_path, mode=self.mode) as file:
                data = self.get_data(caller, args, kwargs)
                await file.write(data)
        except Exception as ex:
            logger.exception("Exception saving file to %s", self.file_path)


class SaveJsonResultToFile(SaveResultToFile):
    """Usually used after ResponseToJson callback."""

    def __init__(self, file_path: str, mode: str = "w") -> None:
        super().__init__(file_path, mode=mode)

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects data (caller.result in super) to be json."""
        data = super().get_data(caller, *args, **kwargs)
        json_data = json.dumps(data, indent=2)
        return json_data


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
        # data: Optional[Dict] = {}
        # if self.data_location == "job":
        job: "EsiJob" = caller.context.get("esi_job", None)
        if job is not None:
            data = job.result
        if data is None or not data:
            logger.warning(
                "Could not get result data from esi_job. job: %s action: %s",
                job,
                caller,
            )
        json_data = json.dumps(data, indent=2)
        return json_data


class ResultToEsiJob(AiohttpActionCallback):
    """Copies result to EsiJob for use outside of event loop"""

    def __init__(self) -> None:
        super().__init__()

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: "EsiJob" = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        esi_job.result["result"] = caller.result


class ResponseToEsiJob(AiohttpActionCallback):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        esi_job: "EsiJob" = caller.context.get("esi_job", None)
        if esi_job is None:
            raise ValueError(f"EsiJob was not attatched to {caller}")
        if caller.response is not None:
            esi_job.result["response"] = response_to_json(caller.response)


def response_to_json(response: aiohttp.ClientResponse) -> Dict:
    # TODO move this to AiohttpActions
    # TODO change name of Aiohttp callback from responsetojson to resulttojson
    # TODO make this a callback, figure out how to assign. attrgetter and a list of args?

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
    return data
