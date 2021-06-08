from datetime import timedelta
from logging import Logger
from typing import List

import pytest
from aiohttp import ClientResponseError, ClientSession
from rich import inspect, print

from eve_esi_jobs.aiohttp_queue import (
    AiohttpRequest,
    AiohttpRequestQueue,
    AiohttpRequestQueueException,
    AiohttpRequestWorker,
    RateLimiter,
    get_pages_requests,
)
from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.operation_manifest import OperationManifest
from eve_esi_jobs.sources import EsiRemoteSource


def test_aiohttp_request_queue(operation_manifest: OperationManifest, logger: Logger):
    remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
    runner = AiohttpRequestQueue()

    job = example_jobs.get_industry_facilities()
    request_1 = remote_source.request_from_job(job)
    task_exceptions = runner.do_request_queue([request_1])
    assert request_1.response_meta.status == 200
    assert len(request_1.data) > 5
    assert isinstance(task_exceptions, dict)
    assert not task_exceptions


def test_bad_request(operation_manifest: OperationManifest, logger: Logger):
    remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
    runner = AiohttpRequestQueue()
    bad_job = example_jobs.get_markets_region_id_history(region_id=10000002, type_id=0)
    bad_request = remote_source.request_from_job(bad_job)
    task_exceptions = runner.do_request_queue([bad_request])
    assert bad_request.response_meta.status == 404
    print(type(bad_request.data), bad_request.data)
    expected_data = '{"error":"Type not found!"}'
    assert isinstance(bad_request.data, str)
    assert bad_request.data == expected_data
    assert isinstance(task_exceptions, dict)
    assert not task_exceptions


def test_bad_request_raise_exception(
    operation_manifest: OperationManifest, logger: Logger
):
    remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
    runner = AiohttpRequestQueue()
    bad_job = example_jobs.get_markets_region_id_history(region_id=10000002, type_id=0)
    bad_request = remote_source.request_from_job(bad_job)
    bad_request.kwargs = {"raise_for_status": True}
    task_exceptions = runner.do_request_queue([bad_request])
    assert bad_request.response_meta is None
    assert isinstance(task_exceptions, dict)
    assert task_exceptions
    exception: AiohttpRequestQueueException = task_exceptions[str(bad_request.uid)]
    assert isinstance(exception, AiohttpRequestQueueException)
    origin: ClientResponseError = exception.original_exception
    assert origin.status == 404


# TODO make test for request copy


def test_paged_data(operation_manifest: OperationManifest, logger: Logger):
    # TODO move to remote source tests
    remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
    runner = AiohttpRequestQueue()
    job = example_jobs.get_contracts_public_region_id(10000002)
    request_1 = remote_source.request_from_job(job)
    task_exceptions = runner.do_request_queue([request_1])
    assert request_1.response_meta.status == 200
    assert len(request_1.data) == 1000
    assert isinstance(task_exceptions, dict)
    assert not task_exceptions
    request_pages: List[AiohttpRequest] = get_pages_requests(request_1)
    limiter = RateLimiter(10)
    pages_task_exceptions = runner.do_request_queue(
        request_pages, limiter=limiter, debug=True
    )
    assert not pages_task_exceptions
    for page in request_pages:
        assert str(page.params["page"]) == page.id_
        assert page.response_meta.status == 200
        assert len(page.data) > 1


@pytest.mark.asyncio
async def test_request(operation_manifest: OperationManifest, logger: Logger):
    job = example_jobs.get_industry_facilities()
    remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
    request = remote_source.request_from_job(job)
    async with ClientSession() as session:
        await request.make_request(session, None)
    # print(request.response_meta)
    assert request.response_meta is not None
    assert request.data is not None

    # assert False

    job = example_jobs.get_contracts_public_region_id(10000002)
    request = remote_source.request_from_job(job)
    async with ClientSession() as session:
        await request.make_request(session, None)
    # print(request.response_meta)
    assert request.response_meta is not None
    assert request.data is not None
    # print("item count = ", len(request.data))
    # assert False


# @pytest.mark.asyncio
# async def test_request_pages(operation_manifest: OperationManifest, logger: Logger):
#     job = example_jobs.get_contracts_public_region_id(10000002)
#     remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
#     request = remote_source.request_from_job(job)
#     async with ClientSession() as session:
#         await request.make_request(session, None)
#     assert request.response_meta is not None
#     assert len(request.data) == 1000
#     request_pages: List[AiohttpRequest] = get_pages_requests(request)
#     assert request_pages is not None
#     limiter = RateLimiter(5, timedelta(seconds=1))

#     worker_count = 10
#     workers: List[AiohttpRequestWorker] = [
#         AiohttpRequestWorker() for _ in range(worker_count)
#     ]
#     runner = RequestQueueRunner()
#     await runner.queue_runner_simple(
#         request_pages, session_kwargs={}, workers=workers, limiter=limiter
#     )
#     count = sum([len(x.data) for x in request_pages])
#     print(count)
#     assert count > (len(request_pages) - 1) * 1000


# def test_request_pages_no_mark(operation_manifest: OperationManifest, logger: Logger):
#     job = example_jobs.get_contracts_public_region_id(10000002)
#     remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
#     request = remote_source.request_from_job(job)
#     limiter = RateLimiter(3)
#     runner = RequestQueueRunner()
#     runner.do_queue_simple(
#         [request], session_kwargs={}, workers=[AiohttpRequestWorker()], limiter=limiter
#     )
#     request_pages: List[AiohttpRequest] = get_pages_requests(request)
#     worker_count = 5
#     workers: List[AiohttpRequestWorker] = [
#         AiohttpRequestWorker() for _ in range(worker_count)
#     ]
#     runner.do_queue_simple(
#         request_pages, session_kwargs={}, workers=workers, limiter=limiter
#     )
#     count = sum([len(x.data) for x in request_pages])
#     print(count)
#     assert count > (len(request_pages) - 1) * 1000
