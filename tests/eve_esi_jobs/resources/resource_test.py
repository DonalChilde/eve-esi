"""These tests are not meant to be run during normal testing.

Uncomment the tests below to update test resources.
"""
from pathlib import Path
from typing import Callable, Sequence

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import DefaultCallbackProvider
from eve_esi_jobs.eve_esi_jobs import serialize_job, serialize_work_order
from eve_esi_jobs.examples import callback_collections, jobs, work_orders
from eve_esi_jobs.typer_cli.cli_helpers import save_string

# def test_job_examples():
#     parent_path = Path(__file__).parent
#     output_path = parent_path / Path("jobs")
#     jobs_list: Sequence[Callable] = [
#         jobs.get_industry_facilities,
#         jobs.get_industry_systems,
#         jobs.post_universe_names,
#     ]
#     default_callbacks = DefaultCallbackProvider().default_callback_collection()
#     for sample in jobs_list:
#         job: models.EsiJob = sample(default_callbacks)
#         file_path = output_path / Path(job.name).with_suffix(".json")
#         job_string = serialize_job(job)
#         save_string(job_string, file_path, parents=True)


# def test_ewo_examples():
#     parent_path = Path(__file__).parent
#     output_path = parent_path / Path("work_orders")
#     ewo_list = [
#         work_orders.response_to_job_json_file,
#         work_orders.result_to_job_json_file,
#         work_orders.result_to_json_file_and_response_to_json_file,
#         work_orders.result_and_response_to_job_json_file,
#         work_orders.result_to_json_file,
#         work_orders.result_to_csv_file,
#         work_orders.result_with_pages_to_json_file,
#     ]

#     for sample in ewo_list:
#         ewo: models.EsiWorkOrder = sample()
#         file_path = output_path / Path(ewo.name).with_suffix(".json")
#         ewo_string = serialize_work_order(ewo)
#         save_string(ewo_string, file_path, parents=True)


# def test_callback_collections():
#     parent_path = Path(__file__).parent
#     output_path = parent_path / Path("callback_collections")
#     jobs_list: Sequence[Callable] = [
#         ("no_file_output", callback_collections.no_file_output),
#         (
#             "generic_save_result_to_json",
#             callback_collections.generic_save_result_to_json,
#         ),
#         (
#             "generic_save_result_and_job_to_json",
#             callback_collections.generic_save_result_and_job_to_json,
#         ),
#     ]

#     for sample in jobs_list:
#         callbacks: models.CallbackCollection = sample[1]()
#         file_path = output_path / Path(sample[0]).with_suffix(".json")
#         data_string = callbacks.json(indent=2)
#         save_string(data_string, file_path, parents=True)
