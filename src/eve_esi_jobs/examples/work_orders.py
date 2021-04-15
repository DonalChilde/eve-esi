import logging

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import DefaultCallbackFactory
from eve_esi_jobs.examples.jobs import get_markets_region_id_history

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def example_workorder():
    callback_factory = DefaultCallbackFactory
    region_id = 10000002
    type_id = 34
    work_order = models.EsiWorkOrder(
        name="example_workorder",
        parent_path_template="samples/workorder_output/${ewo_name}",
        description=(
            "An example of a workorder, with a collection of "
            "jobs whose output is gathered under a file path defined in the workorder."
        ),
    )
    job = get_markets_region_id_history(
        region_id, type_id, callback_factory.default_callback_collection()
    )
    job.name = "Save market history as json"
    job.id_ = 1
    job.description = (
        "Get the market history for Tritainium in The Forge "
        "region, and save it to a json file."
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={
                "file_path": "${esi_job_id_}/market-history-${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    work_order.jobs.append(job)
    #####
    job_2 = get_markets_region_id_history(
        region_id, type_id, callback_factory.default_callback_collection()
    )
    job_2.name = "Save market history and job as json"
    job_2.id_ = 2
    job_2.description = (
        "Get the market history for Tritainium in The Forge "
        "region, and save it to a json file. Also save the job,"
        " including the response metadata, to a separate json file."
    )
    job_2.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "${esi_job_id_}/market-history-${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job_2.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={
                "file_path": "${esi_job_id_}/market-history-${region_id}-${type_id}.json"
            },
        )
    )
    work_order.jobs.append(job_2)
    #####
    job_3 = get_markets_region_id_history(
        region_id, type_id, callback_factory.default_callback_collection()
    )
    job_3.name = "Save market history as csv and job with data as json"
    job_3.id_ = 3
    job_3.description = (
        "Get the market history for Tritainium in The Forge "
        "region, and save it to a csv file. The region_id and type_id added to each row, "
        "and the columns are given a custom order. "
        "Also save the job, including the response metadata and the result data, "
        "to a separate json file."
    )
    job_3.callbacks.success.append(models.JobCallback(callback_id="result_to_esi_job"))
    job_3.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "${esi_job_id_}/market-history-${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job_3.callbacks.success.append(
        models.JobCallback(
            callback_id="save_list_of_dict_result_to_csv_file",
            kwargs={
                "additional_fields": {"region_id": 10000002, "type_id": 34},
                "field_names": [
                    "date",
                    "average",
                    "highest",
                    "lowest",
                    "order_count",
                    "volume",
                    "region_id",
                    "type_id",
                ],
                "file_path": "${esi_job_id_}/market-history-${region_id}-${type_id}.csv",
            },
        )
    )
    work_order.jobs.append(job_3)
    #####
    job_4 = models.EsiJob(
        name="get paged data",
        description="Get the all the pages from a paged api.",
        id_=4,
        op_id="get_contracts_public_region_id",
        parameters={"region_id": 10000002},
        callbacks=callback_factory.default_callback_collection(),
    )
    job_4.callbacks.success.append(models.JobCallback(callback_id="check_for_pages"))
    job_4.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "${esi_job_id_}/public-contracts/${region_id}.json"},
        )
    )
    work_order.jobs.append(job_4)
    return work_order


def response_to_job_json_file():
    work_order = models.EsiWorkOrder(
        name="response_to_job_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving a completed job to a json file,"
            " including the response data. Result data intentionaly left out."
        ),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "data/market-history/${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_to_job_json_file():
    work_order = models.EsiWorkOrder(
        name="result_to_job_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving a completed job to a json file, with result data"
        ),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(models.JobCallback(callback_id="result_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "data/market-history/${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_to_json_file_and_response_to_json_file():
    work_order = models.EsiWorkOrder(
        name="result_to_json_file_and_response_to_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving the raw results to a json file,"
            " and the job with response data to a separate json file"
        ),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "data/market-history/${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/market-history/${region_id}-${type_id}.json"},
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_and_response_to_job_json_file():
    work_order = models.EsiWorkOrder(
        name="result_and_response_to_job_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving a completed job to a json file,"
            " with result and response data"
        ),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(models.JobCallback(callback_id="result_to_esi_job"))
    job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "data/market-history/${region_id}-${type_id}-esi-job.json"
            },
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_to_json_file():
    work_order = models.EsiWorkOrder(
        name="result_to_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=("An example of saving the raw results to a json file."),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )

    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/market-history/${region_id}-${type_id}.json"},
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_to_csv_file():
    work_order = models.EsiWorkOrder(
        name="result_to_csv_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving the json results to a csv file. Also, shows "
            "reordering columns, and adding additional columns"
        ),
    )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 34},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )

    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_list_of_dict_result_to_csv_file",
            kwargs={
                "additional_fields": {"region_id": 10000002, "type_id": 34},
                "field_names": [
                    "date",
                    "average",
                    "highest",
                    "lowest",
                    "order_count",
                    "volume",
                    "region_id",
                    "type_id",
                ],
                "file_path": "data/market-history/${region_id}-${type_id}.csv",
            },
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order


def result_with_pages_to_json_file():
    work_order = models.EsiWorkOrder(
        name="result_with_pages_to_json_file",
        parent_path_template="samples/order_output/${ewo_name}",
        description=(
            "An example of saving the raw results with a paged api to a json file."
        ),
    )
    job = models.EsiJob(
        op_id="get_contracts_public_region_id",
        parameters={"region_id": 10000002},
    )
    work_order.jobs.append(job)
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(models.JobCallback(callback_id="check_for_pages"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/public-contracts/${region_id}.json"},
        )
    )
    job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return work_order
