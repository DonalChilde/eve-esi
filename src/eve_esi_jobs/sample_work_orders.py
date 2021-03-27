from rich import inspect

from eve_esi_jobs import models


def response_to_job():
    work_order = models.EsiWorkOrder()
    job = models.EsiJob(op_id="get_markets_region_id_history")
    work_order.jobs.append(job)
    work_order.name = "response_to_job"
    work_order.parent_path_template = "samples/order_output/${ewo_name}"
    # job.op_id = "get_markets_region_id_history"
    job.retry_limit = 1
    job.parameters = {"region_id": 10000002, "type_id": 34}
    job.result_callbacks.success.append(
        models.JobCallback(callback_id="result_to_json")
    )
    job.result_callbacks.success.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    job.result_callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_result_to_file",
            config={
                "file_path_template": "data/market-history/${region_id}-${type_id}.json"
            },
        )
    )
    return work_order
