"""These tests are not meant to be run during normal testing.

Uncomment the tests below to update test resources.
"""
from pathlib import Path
from typing import Callable, Sequence

from eve_esi_jobs import models
from eve_esi_jobs.eve_esi_jobs import serialize_job, serialize_work_order
from eve_esi_jobs.examples import callback_collections, jobs, work_orders
from eve_esi_jobs.model_helpers import default_callback_collection
from eve_esi_jobs.typer_cli.cli_helpers import save_string

REFRESH_RESOURCES = False


def test_job_examples():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("jobs")
    jobs_list: Sequence[Callable] = [
        jobs.get_industry_facilities,
        jobs.get_industry_systems,
        jobs.post_universe_names,
    ]
    for sample in jobs_list:
        job: models.EsiJob = sample()
        file_path = output_path / Path(job.name).with_suffix(".json")
        job_string = serialize_job(job)
        save_string(job_string, file_path, parents=True)


def test_ewo_examples():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("work_orders")
    ewo_list = [
        work_orders.example_workorder,
        work_orders.response_to_job_json_file,
        work_orders.result_to_job_json_file,
        work_orders.result_to_json_file_and_response_to_json_file,
        work_orders.result_and_response_to_job_json_file,
        work_orders.result_to_json_file,
        work_orders.result_to_csv_file,
        work_orders.result_with_pages_to_json_file,
    ]
    for sample in ewo_list:
        ewo: models.EsiWorkOrder = sample()
        file_path = output_path / Path(ewo.name).with_suffix(".json")
        ewo_string = serialize_work_order(ewo)
        save_string(ewo_string, file_path, parents=True)


def test_callback_collections():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("callback_collections")
    callbacks_list: Sequence[Callable] = [
        ("no_file_output", callback_collections.no_file_output),
        (
            "generic_save_result_to_json",
            callback_collections.generic_save_result_to_json,
        ),
        (
            "generic_save_result_and_job_to_json",
            callback_collections.generic_save_result_and_job_to_json,
        ),
    ]
    for sample in callbacks_list:
        callbacks: models.CallbackCollection = sample[1]()
        file_path = output_path / Path(sample[0]).with_suffix(".json")
        data_string = callbacks.json(indent=2)
        save_string(data_string, file_path, parents=True)


def test_bad_workorders():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("bad_work_orders")
    ewo_list = [bad_status_workorder, bad_validation_workorder]
    for sample in ewo_list:
        ewo: models.EsiWorkOrder = sample()
        file_path = output_path / Path(ewo.name).with_suffix(".json")
        ewo_string = serialize_work_order(ewo)
        save_string(ewo_string, file_path, parents=True)


def test_bad_jobs():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("bad_jobs")
    jobs_list = [bad_parameter_job, missing_parameter_job]
    for sample in jobs_list:
        job: models.EsiJob = sample()
        file_path = output_path / Path(job.name).with_suffix(".json")
        job_string = serialize_job(job)
        save_string(job_string, file_path, parents=True)


def bad_status_workorder():
    ewo = models.EsiWorkOrder(
        name="bad-status-workorder",
        description=(
            "A workorder that contains jobs that will fail on the server "
            "in various ways."
        ),
        id_="bad-status-workorder",
        output_path="samples/workorder_output/${ewo_name}",
    )
    ewo.jobs.append(bad_parameter_job())
    return ewo


def bad_validation_workorder():
    ewo = models.EsiWorkOrder(
        name="bad-validation-workorder",
        description="A workorder that contains jobs that will fail validation.",
        id_="bad-validation-workorder",
        output_path="samples/workorder_output/${ewo_name}",
    )
    ewo.jobs.append(missing_parameter_job())
    return ewo


def missing_parameter_job():
    job = models.EsiJob(
        name="missing-parameter",
        description="A job with a missing parameter, should result in a validation failure.",
        id_="missing-parameter",
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002},
        callbacks=default_callback_collection(),
    )
    return job


def bad_parameter_job():
    job = models.EsiJob(
        name="bad-parameter",
        description="A job with a bad parameter, should result in a 400 bad request.",
        id_="bad-parameter",
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 0},
        callbacks=default_callback_collection(),
    )
    return job
