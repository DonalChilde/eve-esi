import asyncio
from logging import Logger
from pathlib import Path
from typing import Dict

import pytest
from aiohttp import ClientSession
from rich import print
from tests.eve_esi_jobs.conftest import FileResource

from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.models import EsiJob
from eve_esi_jobs.operation_manifest import OperationManifest

# @pytest.mark.asyncio
# async def test_queue_worker(
#     jobs: Dict[str, FileResource],
#     operation_manifest: OperationManifest,
#     test_app_dir: Path,
#     logger: Logger,
# ):
#     job = EsiJob.deserialize_yaml(jobs["get_industry_facilities.yaml"].data)
#     output_path = test_app_dir / Path("test_queue_worker")
#     job.update_attributes({"ewo_output_path": str(output_path)})
#     JobPreprocessor().pre_process_job(job)
#     async with ClientSession() as session:
#         limiter = RateLimiter(1)
#         remote_source = EsiRemoteSource(
#             session=session, limiter=limiter, operation_manifest=operation_manifest
#         )
#         worker = JobQueueWorker(None, remote_source)
#         await worker.do_job(job)
#     assert job.result.response.status == 200
#     assert len(job.result.data) > 10
#     files = list(output_path.glob("**/*.json"))
#     assert len(files) == 2
#     for file in files:
#         assert file.stat().st_size > 5


# @pytest.mark.asyncio
# async def test_job_runner(
#     jobs: Dict[str, FileResource],
#     operation_manifest: OperationManifest,
#     test_app_dir: Path,
# ):
#     job = EsiJob.deserialize_yaml(jobs["get_industry_facilities.yaml"].data)
#     output_path = test_app_dir / Path("test_job_runner")
#     job.update_attributes({"ewo_output_path": str(output_path)})
#     async with ClientSession() as session:
#         limiter = RateLimiter(1)
#         remote_source = EsiRemoteSource(
#             session=session, limiter=limiter, operation_manifest=operation_manifest
#         )

#         await job_runner(job, None, remote_source)
#     assert job.result.response.status == 200
#     assert len(job.result.data) > 10
#     files = list(output_path.glob("**/*.json"))
#     assert len(files) == 2
#     for file in files:
#         assert file.stat().st_size > 5


# @pytest.mark.asyncio
# async def test_queue_runner(
#     jobs: Dict[str, FileResource],
#     operation_manifest: OperationManifest,
#     test_app_dir: Path,
#     logger: Logger,
# ):
#     logger.info("in the test")
#     job_1 = EsiJob.deserialize_yaml(jobs["get_industry_facilities.yaml"].data)
#     job_2 = EsiJob.deserialize_json(jobs["get_industry_systems.json"].data)
#     test_jobs = [job_1, job_2]
#     output_path = test_app_dir / Path("test_job_runner")
#     job_preprocessor = JobPreprocessor()
#     for job in test_jobs:
#         job.update_attributes({"ewo_output_path": str(output_path)})
#         job_preprocessor.pre_process_job(job)
#     await queue_runner(jobs=test_jobs, operation_manifest=operation_manifest)
#     assert job_1.result.response.status == 200
#     assert len(job_1.result.data) > 10
#     assert job_2.result.response.status == 200
#     assert len(job_2.result.data) > 10
#     files = list(output_path.glob("**/*.json"))
#     assert len(files) == 4
#     for file in files:
#         assert file.stat().st_size > 5


# def test_do_queue_runner(
#     jobs: Dict[str, FileResource],
#     operation_manifest: OperationManifest,
#     test_app_dir: Path,
#     logger: Logger,
# ):
#     job_1 = EsiJob.deserialize_yaml(jobs["get_industry_facilities.yaml"].data)
#     job_2 = EsiJob.deserialize_json(jobs["get_industry_systems.json"].data)
#     test_jobs = [job_1, job_2]
#     output_path = test_app_dir / Path("test_job_runner")
#     job_preprocessor = JobPreprocessor()
#     for job in test_jobs:
#         job.update_attributes({"ewo_output_path": str(output_path)})
#         job_preprocessor.pre_process_job(job)
#     do_queue_runner(
#         jobs=test_jobs,
#         operation_manifest=operation_manifest,
#         observers=[LoggingObserver()],
#     )
#     assert job_1.result.response.status == 200
#     assert job_2.result.response.status == 200
#     files = list(output_path.glob("**/*.json"))
#     assert len(files) == 4
#     for file in files:
#         assert file.stat().st_size > 5


# def test_paged_request(
#     operation_manifest: OperationManifest,
#     test_app_dir: Path,
#     logger: Logger,
# ):
#     job = example_jobs.get_contracts_public_region_id(10000002)
#     output_path = test_app_dir / Path("test_paged_request")
#     job_preprocessor = JobPreprocessor()
#     job.update_attributes({"ewo_output_path": str(output_path)})
#     job_preprocessor.pre_process_job(job)
#     do_queue_runner(
#         jobs=[job],
#         operation_manifest=operation_manifest,
#         observers=[LoggingObserver()],
#     )
#     assert job.result.response.status == 200
#     files = list(output_path.glob("**/*.json"))
#     assert len(files) == 1
#     for file in files:
#         assert file.stat().st_size > 5
