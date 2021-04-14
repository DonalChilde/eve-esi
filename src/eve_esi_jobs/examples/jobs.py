from typing import Optional

from eve_esi_jobs import models
from eve_esi_jobs.callback_manifest import DefaultCallbackProvider


def get_industry_facilities(
    callbacks: Optional[models.CallbackCollection] = None,
):
    if callbacks is None:
        callbacks = DefaultCallbackProvider().default_callback_collection()
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={"file_path": "data/industry-facilities-esi-job.json"},
            )
        )
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_json_result_to_file",
                kwargs={"file_path": "data/industry-facilities.json"},
            )
        )
    job = models.EsiJob(
        op_id="get_industry_facilities",
        name="get_industry_facilities",
        callbacks=callbacks,
    )
    return job


def get_industry_systems(
    callbacks: Optional[models.CallbackCollection] = None,
):
    if callbacks is None:
        callbacks = DefaultCallbackProvider().default_callback_collection()
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={"file_path": "data/industry-systems-esi-job.json"},
            )
        )
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_json_result_to_file",
                kwargs={"file_path": "data/industry-systems.json"},
            )
        )
    job = models.EsiJob(
        op_id="get_industry_systems",
        name="get_industry_systems",
        callbacks=callbacks,
    )
    return job


def post_universe_names(
    callbacks: Optional[models.CallbackCollection] = None,
):
    if callbacks is None:
        callbacks = DefaultCallbackProvider().default_callback_collection()
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={
                    "file_path": "data/post_universe_names-${esi_job_uid}-esi-job.json"
                },
            )
        )
        callbacks.success.append(
            models.JobCallback(
                callback_id="save_json_result_to_file",
                kwargs={"file_path": "data/post_universe_names-${esi_job_uid}.json"},
            )
        )
    job = models.EsiJob(
        op_id="post_universe_names",
        name="post_universe_names",
        callbacks=callbacks,
    )
    job.parameters = {"ids": [95465499, 30000142]}
    return job
