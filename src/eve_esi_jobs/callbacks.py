"""foo"""
import json
import logging
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

from eve_esi_jobs.models import EsiJob, EsiJobResult

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
# TODO callback to generate market history summary

DEFAULT_CALLBACKS: ActionCallbacks = ActionCallbacks(
    success=[ResponseContentToJson(), LogSuccess()],
    retry=[LogRetry()],
    fail=[LogFail()],
)


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
        esi_job.result.response = caller.response_meta_to_json()
        esi_job.result.work_order_id = esi_job.get_params().get("ewo_id", "")  # type: ignore
        esi_job.result.work_order_name = esi_job.get_params().get("ewo_name", "")  # type: ignore
