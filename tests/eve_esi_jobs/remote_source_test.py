import asyncio
from typing import Dict

import pytest
from aiohttp import ClientSession
from rich import print
from tests.eve_esi_jobs.conftest import FileResource

from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.exceptions import DataUnchangedException
from eve_esi_jobs.models import EsiJob
from eve_esi_jobs.operation_manifest import OperationManifest
from eve_esi_jobs.sources import EsiRemoteSource, RateLimiter


@pytest.mark.asyncio
async def test_remote_source(
    jobs: Dict[str, FileResource], operation_manifest: OperationManifest
):
    job = EsiJob.deserialize_yaml(jobs["get_industry_facilities.yaml"].data)
    # print(job)
    assert job.op_id == "get_industry_facilities"
    async with ClientSession() as session:

        remote_source = EsiRemoteSource(operation_manifest=operation_manifest)
        result = await remote_source.do_job(job, etag=None, session=session)

    # print(result.data)
    assert "facility_id" in result.data[0]


@pytest.mark.asyncio
async def test_forced_304(
    jobs: Dict[str, FileResource], operation_manifest: OperationManifest
):
    job = example_jobs.get_markets_region_id_history(10000002, 34)
    assert job.op_id == "get_markets_region_id_history"
    limiter = RateLimiter(0.3)
    async with ClientSession() as session:
        remote_source = EsiRemoteSource(
            limiter=limiter, operation_manifest=operation_manifest
        )
        result = await remote_source.do_job(job, session=session)

    assert "average" in result.data[0]
    assert result.response.status == 200

    etag = result.response.get_response_header("Etag")
    assert etag is not None
    print("etag", etag)
    # Normally a 304 would only happen after getting an etag
    # from a result retrieved from the local source. The remote
    # source does not update the result in the case of a 304, resulting
    # in a DataUnchangedException.

    # This will fail sometimes even when the calls are too close together.

    async with ClientSession() as session:
        remote_source = EsiRemoteSource(
            limiter=limiter, operation_manifest=operation_manifest
        )
        with pytest.raises(DataUnchangedException):
            result = await remote_source.do_job(job, session=session, etag=etag)
