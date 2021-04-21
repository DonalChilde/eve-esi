import logging
from typing import Dict, Optional

from pfmsoft.aiohttp_queue import AiohttpAction, AiohttpActionCallback
from pfmsoft.aiohttp_queue.callbacks import SaveResultToFile

from eve_esi_jobs.models import EsiJob, EsiJobResult

# pylint: disable=useless-super-delegation

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
        return data_string


class ResultToEsiJob(AiohttpActionCallback):
    """Copies result to `EsiJob` for use outside of event loop"""

    def __init__(self) -> None:
        super().__init__()

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        _, _ = args, kwargs
        # NOTE this can be dropped when aiohttp-queue implements exception catch fail logic.
        try:
            esi_job: "EsiJob" = caller.context.get("esi_job", None)
            if esi_job is None:
                raise ValueError(f"EsiJob was not attatched to {caller}")
            if esi_job.result is None:
                esi_job.result = EsiJobResult()
            esi_job.result.data = caller.result
            job_attributes = esi_job.attributes()
            esi_job.result.attempts = caller.attempts
            esi_job.result.work_order_id = job_attributes.get("ewo_id", "")  # type: ignore
            esi_job.result.work_order_name = job_attributes.get("ewo_name", "")  # type: ignore
            esi_job.result.work_order_uid = job_attributes.get("ewo_uid", "")
        except Exception as ex:
            self.callback_fail(caller, f"{ex.__class__.__name__} {ex}")
            raise ex


class ResponseToEsiJob(AiohttpActionCallback):
    """Copies response info to the `EsiJob` in json format."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        _, _ = args, kwargs
        # NOTE this can be dropped when aiohttp-queue implements exception catch fail logic.
        try:
            esi_job: EsiJob = caller.context.get("esi_job", None)
            if esi_job is None:
                raise ValueError(f"EsiJob was not attatched to {caller}")
            # if caller.response is not None:
            #     esi_job.result["response"] = response_to_json(caller.response)
            if esi_job.result is None:
                esi_job.result = EsiJobResult()
            esi_job.result.response = caller.response_meta_to_json()
            job_attributes = esi_job.attributes()
            # print(job_attributes)
            esi_job.result.attempts = caller.max_attempts
            esi_job.result.work_order_id = job_attributes.get("ewo_id", "")
            esi_job.result.work_order_name = job_attributes.get("ewo_name", "")
            esi_job.result.work_order_uid = job_attributes.get("ewo_uid", "")
        except Exception as ex:
            self.callback_fail(caller, f"{ex.__class__.__name__} {ex}")
            raise ex


class LogJobFailure(AiohttpActionCallback):
    """surplus to requirements? AiohttpAction will log a failure as well, just without the job info."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        _, _ = args, kwargs
        try:
            esi_job: EsiJob = caller.context.get("esi_job", None)
            logger.warning("Job failed. %r", esi_job)
        except Exception as ex:
            logger.exception("failure in callback %s", ex)
