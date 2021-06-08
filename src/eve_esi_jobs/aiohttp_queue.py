import asyncio
import logging
import re
from asyncio.queues import Queue
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from time import perf_counter_ns
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union
from uuid import UUID, uuid4

from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientResponseError

from eve_esi_jobs.helpers import optional_object

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AiohttpRequestQueueException(Exception):
    def __init__(
        self,
        msg: Optional[str],
        request: "AiohttpRequest",
        exception: Optional[Exception],
    ) -> None:
        if msg is None:
            message = f"Exception {exception!r} during request {request!r}"
        else:
            message = msg
        super().__init__(message)
        self.request = request
        self.original_exception = exception


class RaiseForStatus(AiohttpRequestQueueException):
    def __init__(
        self,
        msg: Optional[str],
        request: "AiohttpRequest",
        exception: ClientResponseError,
    ) -> None:
        if msg is None:
            message = (
                f"Exception raised for status {exception!r} during request {request!r}"
            )
        else:
            message = msg
        super().__init__(message, request, exception)
        self.status_exception = exception


class MaxAttemptsExceeded(AiohttpRequestQueueException):
    def __init__(
        self,
        msg: Optional[str],
        request: "AiohttpRequest",
        exception: Optional[RaiseForStatus],
    ) -> None:
        if msg is None:
            message = f"Max attempts exceeded during request {request!r} {exception!r}"
        else:
            message = msg
        super().__init__(message, request, exception)
        self.status_exception = exception


class RateLimiter:
    """
    Rate is per second.


    """

    def __init__(self, rate, period: timedelta = timedelta(seconds=1)) -> None:
        self.rate = float(rate)
        self.period = period
        self._interval = timedelta(seconds=0)
        self._set_interval()
        self.last_request = datetime.now()
        self.total_delay = timedelta(seconds=0)
        self.total_requests = 0

    def get_delay(self) -> float:
        self.total_requests += 1
        now = datetime.now()
        next_call = self.last_request + self._interval
        if next_call < now:
            delay = timedelta(seconds=0)
        else:
            delay = next_call - now
        self.last_request = next_call
        logger.debug("Issued %s of delay", f"{delay.total_seconds():.3f}")
        self.total_delay += delay
        return delay.total_seconds()

    def adjust_rate(self, change):
        self.rate = float(self.rate + change)
        self._set_interval()

    def adjust_rate_multiplier(self, multiplier):
        self.rate = int(self.rate * multiplier)
        self._set_interval()

    def _set_interval(self):
        try:
            self._interval = timedelta(
                microseconds=(self.period / timedelta(microseconds=1)) / self.rate
            )
            logger.debug("Set interval to %s", self._interval)
        except ZeroDivisionError:
            self._interval = timedelta(seconds=0)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"rate={self.rate!r}, period={self.period!r}"
            ")"
        )


class AiohttpRequestWorker:
    def __init__(
        self,
        retry_status: Optional[List[int]] = None,
        max_attempts: int = 1,
    ) -> None:

        self.uid = uuid4()
        self.task_count = 0
        self.task_exceptions: Dict[str, Exception] = {}
        self.retry_status: List[int] = optional_object(retry_status, list)
        self.max_attempts = max_attempts

    async def consumer(
        self,
        queue: Queue,
        session: ClientSession,
        limiter: Optional[RateLimiter] = None,
    ):
        while True:
            request: AiohttpRequest = await queue.get()
            logger.debug(
                "Worker %s got a request from the queue, %s remaining.",
                self.uid,
                queue.qsize(),
            )
            try:
                self.task_count += 1
                await self.make_request(request, queue, session, limiter)
                # await request.make_request(session, limiter)
            except Exception as ex:  # pylint: disable=broad-except
                # Exceptions are eaten, stored in the worker, and logged
                # so that consumer can caontinue with next item in queue.
                # It is expected that exceptions will be examined after
                # queue complete.
                self.task_exceptions[str(request.uid)] = ex
                logger.exception(
                    "Queue worker %s caught %r from %r", self.uid, ex, request
                )
            queue.task_done()

    async def make_request(
        self,
        request: "AiohttpRequest",
        queue: Optional[Queue],
        session: ClientSession,
        limiter: Optional[RateLimiter],
    ):
        try:
            await request.make_request(session, limiter)
            assert request.response_meta is not None
            if request.response_meta.status in self.retry_status:
                await self.retry_request(request, queue, session, limiter)

        except RaiseForStatus as ex:
            if ex.status_exception.status in self.retry_status:
                await self.retry_request(request, queue, session, limiter, ex)
            else:
                raise ex

    async def retry_request(
        self,
        request: "AiohttpRequest",
        queue: Optional[Queue],
        session: ClientSession,
        limiter: Optional[RateLimiter],
        status_exception: Optional[RaiseForStatus] = None,
    ):
        if limiter is not None:
            limiter.adjust_rate_multiplier(0.90)
        if request.attempts < self.max_attempts:
            logger.info(
                "Retrying request %r, limiter %r, queue %r", request, limiter, queue
            )
            if queue is None:
                await self.make_request(request, queue, session, limiter)
            else:
                await queue.put(request)
        else:
            raise MaxAttemptsExceeded(None, request=request, exception=status_exception)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"uid={self.uid!r}, task_count={self.task_count!r}"
            f"task_exceptions={self.task_exceptions!r}"
            ")"
        )


@dataclass
class ResponseMeta:
    version: str
    status: int
    reason: str
    cookies: str
    response_headers: List[Dict]
    method: str
    url: str
    real_url: str
    request_headers: List[Dict]
    start: int = 0
    end: int = 0
    attempts: int = 0

    def get_response_header(self, key: str) -> Optional[Any]:
        for item in self.response_headers:
            for dict_key, value in item.items():
                if key.lower() == dict_key.lower():
                    return value
        return None

    @classmethod
    def from_response(cls, response: ClientResponse) -> "ResponseMeta":
        request_headers = [
            {key: value} for key, value in response.request_info.headers.items()
        ]
        response_headers = [{key: value} for key, value in response.headers.items()]
        result = ResponseMeta(
            version=str(response.version),
            status=response.status,
            reason=str(response.reason),
            cookies=str(response.cookies),
            response_headers=response_headers,
            method=response.request_info.method,
            url=str(response.request_info.url),
            real_url=str(response.request_info.real_url),
            request_headers=request_headers,
        )
        return result

    @classmethod
    def from_exception(cls, exception: ClientResponseError) -> "ResponseMeta":
        request_headers = [
            {key: value} for key, value in exception.request_info.headers.items()
        ]
        if exception.headers is not None:
            response_headers = [
                {key: value} for key, value in exception.headers.items()
            ]
        else:
            response_headers = []
        result = ResponseMeta(
            version="",
            status=exception.status,
            reason=str(exception.message),
            cookies="",
            response_headers=response_headers,
            method=exception.request_info.method,
            url=str(exception.request_info.url),
            real_url=str(exception.request_info.real_url),
            request_headers=request_headers,
        )
        return result


class ResponseType(Enum):
    JSON = "json"
    TEXT = "text"
    BYTES = "bytes"
    NONE = "none"
    AUTO = "auto"


@dataclass
class AiohttpRequest:
    id_: str
    method: str
    url: str
    uid: UUID = uuid4()
    params: Dict = field(default_factory=dict)
    json: Union[List, Dict] = field(default_factory=dict)
    headers: Dict = field(default_factory=dict)
    kwargs: Dict = field(default_factory=dict)
    response_type: ResponseType = ResponseType.JSON
    response_meta: Optional[ResponseMeta] = None
    data: Optional[Any] = None
    attempts: int = 0

    def as_dict(self) -> Dict[str, Any]:
        """A dict suitable for expanding into an Aiohttp request."""
        # do not submit both json and data to request.
        # FIXME raise an exception for this.
        if "data" in self.kwargs:
            json_data = None
        else:
            json_data = self.json
        kwarg_dict = {
            "method": self.method,
            "url": self.url,
            "params": self.params,
            "json": json_data,
            "headers": self.headers,
        }
        kwarg_dict.update(self.kwargs)
        return kwarg_dict

    def make_copy(self, **kwargs) -> "AiohttpRequest":
        new_request = AiohttpRequest(
            id_=kwargs.get("id_", self.id_),
            method=kwargs.get("method", self.method),
            url=kwargs.get("url", self.url),
            params=kwargs.get("params", deepcopy(self.params)),
            json=kwargs.get("json", deepcopy(self.json)),
            headers=kwargs.get("headers", deepcopy(self.headers)),
            kwargs=kwargs.get("kwargs", deepcopy(self.kwargs)),
            response_type=kwargs.get("response_type", self.response_type),
        )
        return new_request

    async def make_request(
        self,
        session: ClientSession,
        limiter: Optional[RateLimiter],
    ):
        """Make a request.

        With `raise_for_status=False`, `AiohttpRequest.response_meta` will be set from the
        `ClientResponse`, and `AiohttpRequest.data` will be set. In the case of a non 200
        status, `AiohttpRequest.data` will be read from the response as text, no matter the
        `AiohttpRequest.response_type` given.

        With `raise_for_status=True`, `AiohttpRequest.response_meta` and `AiohttpRequest.data`
        will not be set. The `ClientResponseError` will be raised wrapped in a
        `RaiseForStatus` exception.
        """
        start = perf_counter_ns()
        if limiter is not None:
            await asyncio.sleep(limiter.get_delay())

        try:
            async with session.request(**self.as_dict()) as response:
                self.response_meta = ResponseMeta.from_response(response)
                self.attempts += 1
                await self.decode_data(response)
                self.response_meta.start = start
                end = perf_counter_ns()
                self.response_meta.end = end
                logger.debug(
                    "Request completed in %s", f"{(end - start) / 1000000000:.2f}"
                )
        except ClientResponseError as ex:
            status_exception = RaiseForStatus(None, request=self, exception=ex)
            logger.exception("%r", status_exception)
            raise status_exception from ex
        except Exception as ex:
            exception = AiohttpRequestQueueException(None, request=self, exception=ex)
            logger.exception("%r", exception)
            raise exception from ex

    async def decode_data(self, response: ClientResponse):
        if response.status == 200:
            if self.response_type == ResponseType.AUTO:
                self.data = await self.auto_decode(response)
            elif self.response_type == ResponseType.JSON:
                self.data = await response.json()
            elif self.response_type == ResponseType.TEXT:
                self.data = await response.text()
            elif self.response_type == ResponseType.BYTES:
                self.data = await response.read()
            elif self.response_type == ResponseType.NONE:
                self.data = None
            else:
                self.data = None
        else:
            # Set request.data even on errors, in case useful.
            # NOTE this is not done if raise_for_status=True
            self.data = await response.text()

    async def auto_decode(self, response: ClientResponse):
        content_type = response.headers.get("content-type", None)
        if content_type is None:
            if response.status == 200:
                logger.warning(
                    "Content type not found, returning text for request data. %r",
                    response,
                )
            else:
                logger.info(
                    "Content type not found, returning text for request data. %r",
                    response,
                )
            data = await response.text()
            return data
        elif "application/json" in content_type.lower():
            data = await response.json()
            return data
        elif "text/html" in content_type.lower():
            data = await response.text()
            return data
        else:
            logger.warning(
                "unhandled content type %s, returning text for request data %r",
                content_type,
                response,
            )
            data = await response.text()
            return data


class AiohttpRequestQueue:
    def __init__(
        self,
        limiter: Optional[RateLimiter] = RateLimiter(10, timedelta(seconds=1)),
        max_workers: int = 100,
    ) -> None:
        """Do a queue of requests.

        Args are to provide some defaults when specific values not provided.
        The only way to run a non rate limited queue should be to init class with
        limiter = None.
        """
        self.limiter = limiter
        self.max_workers = max_workers

    def calculate_worker_count(self, request_count) -> int:
        """The worker limit is more about local resources than remote server load."""
        # worker_calc = ceil(job_count / 2)
        worker_calc = request_count
        if worker_calc > self.max_workers:
            worker_calc = self.max_workers
        return worker_calc

    async def request_queue_runner(
        self,
        requests: Sequence[AiohttpRequest],
        workers: Optional[List[AiohttpRequestWorker]] = None,
        session: Union[ClientSession, Dict[str, Any], None] = None,
        limiter: Optional[RateLimiter] = None,
    ) -> Dict[str, Exception]:
        if limiter is None:
            limiter = self.limiter
        if workers is None:
            workers = []
            for _ in range(self.calculate_worker_count(len(requests))):
                workers.append(AiohttpRequestWorker())
        start = perf_counter_ns()
        queue: Queue = Queue()
        for request in requests:
            queue.put_nowait(request)
        await self._complete_queue(
            workers=workers,
            queue=queue,
            session=session,
            limiter=limiter,
        )
        worker_report = [
            f"Worker {worker.uid} accomplished {worker.task_count} tasks."
            for worker in workers
        ]
        logger.info("Worker Report: %s", list(worker_report))
        end = perf_counter_ns()
        seconds = (end - start) / 1000000000
        logger.info(
            (
                "%s Actions concurrently completed - took %s seconds, "
                "%s actions per second using %s workers."
            ),
            len(requests),
            f"{seconds:.2f}",
            f"{(len(requests)/seconds):.2f}",
            len(workers),
        )
        task_exceptions = {}
        for worker in workers:
            task_exceptions.update(worker.task_exceptions)
        return task_exceptions

    def make_tasks(
        self,
        workers: List[AiohttpRequestWorker],
        queue: Queue,
        session: ClientSession,
        limiter: Optional[RateLimiter],
    ) -> List[asyncio.Task]:
        worker_tasks: List[asyncio.Task] = []
        for worker in workers:
            worker_tasks.append(
                asyncio.create_task(
                    worker.consumer(queue=queue, session=session, limiter=limiter)
                )
            )
        return worker_tasks

    async def _complete_queue(
        self,
        workers: List[AiohttpRequestWorker],
        queue: Queue,
        limiter: Optional[RateLimiter] = None,
        session: Union[ClientSession, Dict[str, Any], None] = None,
    ):
        if isinstance(session, ClientSession):
            client_session: Optional[ClientSession] = session
            session_kwargs = {}
        elif isinstance(session, dict):
            client_session = None
            session_kwargs = session
        else:
            client_session = None
            session_kwargs = {}
        worker_tasks: List[asyncio.Task] = []
        if client_session is not None:
            worker_tasks = self.make_tasks(
                workers=workers, queue=queue, session=client_session, limiter=limiter
            )
            await queue.join()
        else:
            async with ClientSession(**session_kwargs) as session:
                worker_tasks = self.make_tasks(
                    workers=workers, queue=queue, session=session, limiter=limiter
                )
                await queue.join()
        for worker_task in worker_tasks:
            worker_task.cancel()
        results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        logger.debug("worker results: %r", results)

    def do_request_queue(
        self,
        requests: Sequence[AiohttpRequest],
        workers: Optional[List[AiohttpRequestWorker]] = None,
        session: Union[ClientSession, Dict[str, Any], None] = None,
        limiter: Optional[RateLimiter] = None,
        debug=False,
    ) -> Dict[str, Exception]:
        task_exceptions = asyncio.run(
            self.request_queue_runner(
                requests=requests,
                workers=workers,
                session=session,
                limiter=limiter,
            ),
            debug=debug,
        )
        return task_exceptions

    # def do_queue(
    #     self,
    #     requests: List[AiohttpRequest],
    #     session: ClientSession,
    #     workers: List[AiohttpRequestWorker],
    #     backoff: RateLimiter,
    # ):
    #     asyncio.run(
    #         self.queue_runner(
    #             requests=requests, session=session, workers=workers, backoff=backoff
    #         )
    #     )

    # def do_queue_simple(
    #     self,
    #     requests: List[AiohttpRequest],
    #     session_kwargs: Optional[Dict],
    #     worker_limit: int = 100,
    #     rate_limit: int = 45,
    #     workers: Optional[List[AiohttpRequestWorker]] = None,
    #     limiter: Optional[RateLimiter] = None,
    # ):
    #     asyncio.run(
    #         self.queue_runner_simple(
    #             requests=requests,
    #             session_kwargs=session_kwargs,
    #             worker_limit=worker_limit,
    #             rate_limit=rate_limit,
    #             workers=workers,
    #             limiter=limiter,
    #         )
    #     )

    # async def queue_runner_simple(
    #     self,
    #     requests: List[AiohttpRequest],
    #     session_kwargs: Optional[Dict],
    #     worker_limit: int = 100,
    #     rate_limit: int = 45,
    #     workers: Optional[List[AiohttpRequestWorker]] = None,
    #     limiter: Optional[RateLimiter] = None,
    # ):
    #     session_kwargs = optional_object(session_kwargs, dict)
    #     worker_count = self.calculate_worker_count(len(requests), worker_limit)
    #     if workers is None:
    #         workers = [AiohttpRequestWorker() for _ in range(worker_count)]
    #     if limiter is None:
    #         limiter = RateLimiter(rate_limit)
    #     async with ClientSession(**session_kwargs) as session:
    #         await self.queue_runner(requests, session, workers, limiter)

    # async def queue_runner(
    #     self,
    #     requests: List[AiohttpRequest],
    #     session: ClientSession,
    #     workers: List[AiohttpRequestWorker],
    #     backoff: RateLimiter,
    # ):
    #     start = perf_counter_ns()
    #     queue: Queue = Queue()
    #     worker_tasks: List[asyncio.Task] = []
    #     for worker in workers:
    #         worker_task = asyncio.create_task(worker.consumer(queue, session, backoff))
    #         worker_tasks.append(worker_task)
    #     for request in requests:
    #         queue.put_nowait(request)
    #     await queue.join()
    #     for worker_task in worker_tasks:
    #         worker_task.cancel()
    #     worker_report = [
    #         f"Worker {worker.uid} accomplished {worker.task_count} tasks."
    #         for worker in workers
    #     ]
    #     logger.info("Worker Report: %s", list(worker_report))
    #     await asyncio.gather(*worker_tasks, return_exceptions=True)
    #     end = perf_counter_ns()
    #     seconds = (end - start) / 1000000000
    #     logger.info(
    #         (
    #             "%s Actions concurrently completed - took %s seconds, "
    #             "%s actions per second using %s workers."
    #         ),
    #         len(requests),
    #         f"{seconds:.2f}",
    #         f"{(len(requests)/seconds):.2f}",
    #         len(worker_tasks),
    #     )


# async def request_runner(
#     requests: List[AiohttpRequest],
#     session_kwargs: Dict,
#     backoff: Optional[RateLimiter] = None,
# ):
#     async with ClientSession(**session_kwargs) as session:
#         for request in requests:
#             await request.make_request(session, backoff)


# def do_requests(
#     requests: List[AiohttpRequest],
#     session_kwargs: Dict,
#     backoff: Optional[RateLimiter] = None,
# ):
#     asyncio.run(
#         request_runner(
#             requests=requests, session_kwargs=session_kwargs, backoff=backoff
#         )
#     )


def get_pages_requests(request: AiohttpRequest) -> Optional[List[AiohttpRequest]]:
    """an example of getting paged requests, will be specific to each api."""
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


# class RequestQueueRunner:
#     def __init__(self) -> None:
#         pass

#     def calculate_worker_count(self, job_count, max_workers: int = 100) -> int:
#         """The worker limit is more about local resources than remote server load."""
#         # worker_calc = ceil(job_count / 2)
#         worker_calc = job_count
#         if worker_calc > max_workers:
#             worker_calc = max_workers
#         return worker_calc

#     def do_queue(
#         self,
#         requests: List[AiohttpRequest],
#         session: ClientSession,
#         workers: List[AiohttpRequestWorker],
#         backoff: RateLimiter,
#     ):
#         asyncio.run(
#             self.queue_runner(
#                 requests=requests, session=session, workers=workers, backoff=backoff
#             )
#         )

#     def do_queue_simple(
#         self,
#         requests: List[AiohttpRequest],
#         session_kwargs: Optional[Dict],
#         worker_limit: int = 100,
#         rate_limit: int = 45,
#         workers: Optional[List[AiohttpRequestWorker]] = None,
#         limiter: Optional[RateLimiter] = None,
#     ):
#         asyncio.run(
#             self.queue_runner_simple(
#                 requests=requests,
#                 session_kwargs=session_kwargs,
#                 worker_limit=worker_limit,
#                 rate_limit=rate_limit,
#                 workers=workers,
#                 limiter=limiter,
#             )
#         )

#     async def queue_runner_simple(
#         self,
#         requests: List[AiohttpRequest],
#         session_kwargs: Optional[Dict],
#         worker_limit: int = 100,
#         rate_limit: int = 45,
#         workers: Optional[List[AiohttpRequestWorker]] = None,
#         limiter: Optional[RateLimiter] = None,
#     ):
#         session_kwargs = optional_object(session_kwargs, dict)
#         worker_count = self.calculate_worker_count(len(requests), worker_limit)
#         if workers is None:
#             workers = [AiohttpRequestWorker() for _ in range(worker_count)]
#         if limiter is None:
#             limiter = RateLimiter(rate_limit)
#         async with ClientSession(**session_kwargs) as session:
#             await self.queue_runner(requests, session, workers, limiter)

#     async def queue_runner(
#         self,
#         requests: List[AiohttpRequest],
#         session: ClientSession,
#         workers: List[AiohttpRequestWorker],
#         backoff: RateLimiter,
#     ):
#         start = perf_counter_ns()
#         queue: Queue = Queue()
#         worker_tasks: List[asyncio.Task] = []
#         for worker in workers:
#             worker_task = asyncio.create_task(worker.consumer(queue, session, backoff))
#             worker_tasks.append(worker_task)
#         for request in requests:
#             queue.put_nowait(request)
#         await queue.join()
#         for worker_task in worker_tasks:
#             worker_task.cancel()
#         worker_report = [
#             f"Worker {worker.uid} accomplished {worker.task_count} tasks."
#             for worker in workers
#         ]
#         logger.info("Worker Report: %s", list(worker_report))
#         await asyncio.gather(*worker_tasks, return_exceptions=True)
#         end = perf_counter_ns()
#         seconds = (end - start) / 1000000000
#         logger.info(
#             (
#                 "%s Actions concurrently completed - took %s seconds, "
#                 "%s actions per second using %s workers."
#             ),
#             len(requests),
#             f"{seconds:.2f}",
#             f"{(len(requests)/seconds):.2f}",
#             len(worker_tasks),
#         )


# async def request_queue_runner(
#     requests: List[AiohttpRequest],
#     session: Optional[ClientSession],
#     session_kwargs: Optional[Dict],
#     workers: List[AiohttpRequestWorker],
#     backoff: Optional[RateLimiter] = None,
# ):
#     start = perf_counter_ns()
#     session_kwargs = optional_object(session_kwargs, dict)
#     queue: Queue = Queue()
#     async with ClientSession(**session_kwargs) as session:
#         worker_tasks: List[asyncio.Task] = []
#         for worker in workers:
#             worker_task = asyncio.create_task(worker.consumer(queue, session, backoff))
#             worker_tasks.append(worker_task)
#         for request in requests:
#             queue.put_nowait(request)
#         await queue.join()
#         for worker_task in worker_tasks:
#             worker_task.cancel()
#         worker_report = [
#             f"Worker {worker.uid} accomplished {worker.task_count} tasks."
#             for worker in workers
#         ]
#         logger.info("Worker Report: %s", list(worker_report))
#         await asyncio.gather(*worker_tasks, return_exceptions=True)
#         end = perf_counter_ns()
#         seconds = (end - start) / 1000000000
#         logger.info(
#             (
#                 "%s Actions concurrently completed - took %s seconds, "
#                 "%s actions per second using %s workers."
#             ),
#             len(requests),
#             f"{seconds:.2f}",
#             f"{(len(requests)/seconds):.2f}",
#             len(worker_tasks),
#         )


# def do_request_queue_runner(
#     requests: List[AiohttpRequest],
#     session_kwargs: Dict,
#     workers: List[AiohttpRequestWorker],
#     backoff: Optional[RateLimiter] = None,
# ):

#     asyncio.run(
#         request_queue_runner(
#             requests=requests,
#             session_kwargs=session_kwargs,
#             workers=workers,
#             backoff=backoff,
#         )
#     )


# def get_worker_count(job_count, max_workers: int = 100) -> int:
#     """Try to strike a reasonable balance between speed and DOS."""
#     # worker_calc = ceil(job_count / 2)
#     worker_calc = job_count
#     if worker_calc > max_workers:
#         worker_calc = max_workers
#     return worker_calc
