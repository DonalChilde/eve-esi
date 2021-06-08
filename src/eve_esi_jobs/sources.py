import logging
from pathlib import Path
from string import Template
from time import perf_counter_ns
from typing import List, Optional

from aiohttp import ClientResponseError, ClientSession

from eve_esi_jobs.aiohttp_queue import (
    AiohttpRequest,
    AiohttpRequestQueue,
    AiohttpRequestWorker,
    RaiseForStatus,
    RateLimiter,
    ResponseMeta,
    ResponseType,
)
from eve_esi_jobs.exceptions import (
    BadDataException,
    BadStatusException,
    DataUnchangedException,
    FailedRetryException,
    RetrievalError,
)
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import EsiJob, EsiJobResult
from eve_esi_jobs.operation_manifest import OperationManifest

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class EsiLocalSource:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    async def do_job(self, job: EsiJob) -> Optional[EsiJobResult]:
        try:
            result = await self._get_job_from_source(job)
            return result
        except Exception as ex:
            raise RetrievalError("Error retrieving job from local source.", ex) from ex

    async def _get_job_from_source(self, job: EsiJob) -> Optional[EsiJobResult]:
        job_path = Path(f"{job.op_id}-{job.param_sig()}.json")
        file_path = self.root_path / job_path
        if file_path.exists():
            data = file_path.read_text()
            result = EsiJobResult.deserialize_json(data)
            return result
        return None

    async def store_result(self, result: EsiJobResult):
        try:
            job_path = Path(f"{result.op_id}-{result.param_sig}.json")
            file_path = self.root_path / job_path
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(result.serialize_json())
            return
        except Exception as ex:
            raise RetrievalError("Error saving job to local source.", ex) from ex


class EsiRemoteSource:
    def __init__(
        self,
        operation_manifest: OperationManifest,
        limiter: Optional[RateLimiter] = None,
        max_attempts: int = 3,
    ) -> None:
        self.limiter = optional_object(limiter, RateLimiter, rate=10)
        self.operation_manifest = operation_manifest
        self.max_attempts = max_attempts
        self.retry_list = [500, 503, 504]

    async def do_job(
        self, job: EsiJob, session: ClientSession, etag: Optional[str] = None
    ) -> EsiJobResult:
        request = self.request_from_job(job=job, etag=etag)
        await self.make_request(request, session)
        result = EsiJobResult(
            op_id=job.op_id,
            param_sig=job.param_sig(),
            response=request.response_meta,
            data=request.data,
        )

        return result

    # async def retry_request(self, request: AiohttpRequest, session: ClientSession):
    #     self.limiter.adjust_rate_multiplier(0.90)
    #     while request.attempts < self.max_attempts:
    #         logger.info("Retrying request %r", request)
    #         try:
    #             await request.make_request(session, self.limiter)
    #         except RaiseForStatus as ex:
    #             pass
    #         if request.response_meta.status in [200, 304]:
    #             return
    #         if request.response_meta.status in self.retry_list:
    #             continue
    #         raise BadStatusException(
    #             f"Request to {request.response_meta.url} failed with "
    #             f"{request.response_meta.status}:{request.response_meta.reason}",
    #             request,
    #         )
    #     raise FailedRetryException(
    #         f"Request to {request.response_meta.url} failed with "
    #         f"{request.response_meta.status}:{request.response_meta.reason}",
    #         request,
    #     )

    async def make_request(self, request: AiohttpRequest, session: ClientSession):
        try:
            await request.make_request(session, self.limiter)
            await self.handle_200(request, session)
        except RaiseForStatus as ex:
            if ex.status_exception.status in self.retry_list:
                self.limiter.adjust_rate_multiplier(0.90)
                if request.attempts < self.max_attempts:
                    logger.info(
                        "Retrying request %r, limiter %r", request, self.limiter
                    )
                    await self.make_request(request, session)
                else:
                    raise FailedRetryException(None, ex) from ex

            elif ex.status_exception.status == 304:
                raise DataUnchangedException(None, exception=ex) from ex
            else:
                raise BadStatusException(None, exception=ex) from ex

    def get_pages_requests(
        self, request: AiohttpRequest
    ) -> Optional[List[AiohttpRequest]]:
        """Check for pages, make requests for them."""
        assert request.response_meta is not None
        pages = request.response_meta.get_response_header("x-pages")
        if pages is None or int(pages) == 1:
            return None
        page_int = int(pages)
        requests: List[AiohttpRequest] = []
        for page_number in range(2, page_int + 1):
            new_request = request.make_copy(id_=str(page_number))
            new_request.params["page"] = page_number
            requests.append(new_request)
        return requests

    async def do_page_requests(
        self, requests: List[AiohttpRequest], session: ClientSession
    ):
        worker_count = 10
        workers = [AiohttpRequestWorker() for _ in range(worker_count)]
        runner = AiohttpRequestQueue()
        task_exceptions = await runner.request_queue_runner(
            requests=requests, session=session, limiter=self.limiter
        )
        await runner.queue_runner(
            requests=requests,
            session=session,
            workers=workers,
            backoff=self.limiter,
        )
        # FIXME use new AiohttpRunner, think through returns
        for request in requests:
            assert request.response_meta is not None
            if request.response_meta.status != 200:
                if request.response_meta.status in self.retry_list:
                    self.retry_request(request, session)
                    if request.response_meta.status != 200:
                        raise BadStatusException(
                            f"Error: Paged request to {request.response_meta.url} got status: "
                            f"{request.response_meta.status}: {request.response_meta.reason}",
                            request=request,
                        )
                else:
                    raise BadStatusException(
                        f"Error: Paged request to {request.response_meta.url} got status: "
                        f"{request.response_meta.status}: {request.response_meta.reason}",
                        request=request,
                    )

    async def handle_200(self, request: AiohttpRequest, session: ClientSession):
        assert request.response_meta is not None
        page_requests = self.get_pages_requests(request)
        if page_requests is None:
            return
        try:
            await self.do_page_requests(page_requests, session)
            self.combine_page_results(request, page_requests)
        except ClientResponseError as ex:
            # TODO raise request error signal
            request.response_meta = ResponseMeta.from_exception(ex)
            request.data = None
        finally:
            request.response_meta.end = perf_counter_ns()

    def combine_page_results(
        self, request: AiohttpRequest, page_requests: List[AiohttpRequest]
    ):

        assert request.data is not None
        assert request.response_meta is not None
        try:
            for sub_request in page_requests:
                request.data.extend(sub_request.data)
        except Exception as ex:
            raise BadDataException(
                f"Error adding page data for {request.response_meta.url}. Error was {ex}",
                request=request,
                exception=ex,
            ) from ex

    def request_from_job(
        self,
        job: EsiJob,
        etag: Optional[str] = None,
    ) -> AiohttpRequest:
        op_info = self.operation_manifest.op_info(job.op_id)
        request_params = op_info.request_params_to_locations(job.parameters)
        if etag is not None:
            request_params.header["If-None-Match"] = etag
        url_template = Template(self.operation_manifest.url_template(job.op_id))
        request = AiohttpRequest(
            id_=str(job.uid),
            method=op_info.method,
            url=url_template.substitute(request_params.path),
            params=request_params.query,
            json=request_params.body,
            headers=request_params.header,
            response_type=ResponseType.AUTO,
            kwargs={"raise_for_status": True},
        )
        return request
