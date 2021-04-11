from typing import Optional

from eve_esi_jobs import models


def get_industry_facilities(
    default_callbacks: Optional[models.CallbackCollection] = None,
):
    if default_callbacks is None:
        default_callbacks = models.CallbackCollection()
    else:
        default_callbacks = default_callbacks.copy(deep=True)
    job = models.EsiJob(
        op_id="get_industry_facilities",
        name="get_industry_facilities",
        callbacks=default_callbacks,
    )
    # job.callbacks.success.append(
    #     models.JobCallback(callback_id="response_content_to_json")
    # )
    # job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-facilities-esi-job.json"},
        )
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/industry-facilities.json"},
        )
    )
    # job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    # job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return job


def get_industry_systems(
    default_callbacks: Optional[models.CallbackCollection] = None,
):
    if default_callbacks is None:
        default_callbacks = models.CallbackCollection()
    else:
        default_callbacks = default_callbacks.copy(deep=True)
    job = models.EsiJob(
        op_id="get_industry_systems",
        name="get_industry_systems",
        callbacks=default_callbacks,
    )
    # job.callbacks.success.append(
    #     models.JobCallback(callback_id="response_content_to_json")
    # )
    # job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-systems-esi-job.json"},
        )
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/industry-systems.json"},
        )
    )
    # job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    # job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return job


def post_universe_names(
    default_callbacks: Optional[models.CallbackCollection] = None,
):
    if default_callbacks is None:
        default_callbacks = models.CallbackCollection()
    else:
        default_callbacks = default_callbacks.copy(deep=True)
    job = models.EsiJob(
        op_id="post_universe_names",
        name="post_universe_names",
        callbacks=default_callbacks,
    )
    job.parameters = {"ids": [95465499, 30000142]}
    # job.callbacks.success.append(
    #     models.JobCallback(callback_id="response_content_to_json")
    # )
    # job.callbacks.success.append(models.JobCallback(callback_id="response_to_esi_job"))
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path": "data/post_universe_names-${esi_job_uid}-esi-job.json"
            },
        )
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "data/post_universe_names-${esi_job_uid}.json"},
        )
    )
    # job.callbacks.fail.append(models.JobCallback(callback_id="response_to_esi_job"))
    # job.callbacks.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return job
