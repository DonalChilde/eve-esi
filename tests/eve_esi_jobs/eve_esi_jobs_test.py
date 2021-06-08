import json
from pathlib import Path

from rich import print
from tests.eve_esi_jobs.conftest import FileResource

from eve_esi_jobs.eve_esi_jobs import EveEsiJobs
from eve_esi_jobs.examples import jobs as example_jobs


def test_single_remote_job(logger, esi_schema: FileResource, test_app_dir: Path):
    runner = EveEsiJobs(esi_schema=esi_schema.data, local_source=None)
    job = example_jobs.get_industry_systems()
    overrides = {"ewo_output_path": str(test_app_dir)}
    runner.do_job(job, override_values=overrides)
    assert job.result.response.status == 200
    assert len(job.result.data) > 10


def test_remote_job_queue(logger, esi_schema: FileResource, test_app_dir: Path):
    runner = EveEsiJobs(esi_schema=esi_schema.data, local_source=None)
    job = example_jobs.get_industry_systems()
    job_2 = example_jobs.get_industry_facilities()
    overrides = {"ewo_output_path": str(test_app_dir)}
    runner.do_jobs([job, job_2], override_values=overrides)
    assert job.result.response.status == 200
    assert len(job.result.data) > 10
    assert job_2.result.response.status == 200
    assert len(job_2.result.data) > 10


def test_remote_job_pages(logger, esi_schema: FileResource, test_app_dir: Path):
    runner = EveEsiJobs(esi_schema=esi_schema.data, local_source=None)
    job = example_jobs.get_contracts_public_region_id(10000002)
    overrides = {"ewo_output_path": str(test_app_dir)}
    runner.do_job(job, override_values=overrides)
    assert job.result.response.status == 200
    assert len(job.result.data) > 15000
