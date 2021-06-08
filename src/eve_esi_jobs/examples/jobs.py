from typing import List, Optional

from eve_esi_jobs import models


def get_contracts_public_region_id(
    region_id: int, callbacks: Optional[List[models.JobCallback]] = None
):
    if callbacks is None:
        callbacks = []
        callbacks.append(
            models.JobCallback(
                callback_id="save_result_to_json_file",
                kwargs={
                    "file_path_template": "data/contracts-public-${region_id}.json"
                },
            )
        )
    job = models.EsiJob(
        op_id="get_contracts_public_region_id",
        name="get_contracts_public_region_id",
        callbacks=callbacks,
    )
    job.parameters = {"region_id": region_id}
    return job


def get_markets_region_id_history(
    region_id: int,
    type_id: int,
    callbacks: Optional[List[models.JobCallback]] = None,
):
    if callbacks is None:
        callbacks = []
        callbacks.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={
                    "file_path_template": "data/market-history-${region_id}-${type_id}-esi-job.json"
                },
            )
        )
        callbacks.append(
            models.JobCallback(
                callback_id="save_result_to_json_file",
                kwargs={
                    "file_path_template": "data/market-history-${region_id}-${type_id}.json"
                },
            )
        )
    job = models.EsiJob(
        op_id="get_markets_region_id_history",
        name="get_markets_region_id_history",
        callbacks=callbacks,
    )
    job.parameters = {"region_id": region_id, "type_id": type_id}
    return job


def get_industry_facilities(
    callbacks: Optional[List[models.JobCallback]] = None,
):
    if callbacks is None:
        callbacks = []
        callbacks.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={"file_path_template": "data/industry-facilities-esi-job.json"},
            )
        )
        callbacks.append(
            models.JobCallback(
                callback_id="save_result_to_json_file",
                kwargs={"file_path_template": "data/industry-facilities.json"},
            )
        )
    job = models.EsiJob(
        op_id="get_industry_facilities",
        name="get_industry_facilities",
        callbacks=callbacks,
    )
    return job


def get_industry_systems(
    callbacks: Optional[List[models.JobCallback]] = None,
):
    if callbacks is None:
        callbacks = []
        callbacks.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={"file_path_template": "data/industry-systems-esi-job.json"},
            )
        )
        callbacks.append(
            models.JobCallback(
                callback_id="save_result_to_json_file",
                kwargs={"file_path_template": "data/industry-systems.json"},
            )
        )
    job = models.EsiJob(
        op_id="get_industry_systems",
        name="get_industry_systems",
        callbacks=callbacks,
    )
    return job


def post_universe_names(
    callbacks: Optional[List[models.JobCallback]] = None,
):
    if callbacks is None:
        callbacks = []
        callbacks.append(
            models.JobCallback(
                callback_id="save_esi_job_to_json_file",
                kwargs={
                    "file_path_template": "data/post_universe_names-${esi_job_uid}-esi-job.json"
                },
            )
        )
        callbacks.append(
            models.JobCallback(
                callback_id="save_result_to_json_file",
                kwargs={
                    "file_path_template": "data/post_universe_names-${esi_job_uid}.json"
                },
            )
        )
    job = models.EsiJob(
        op_id="post_universe_names",
        name="post_universe_names",
        callbacks=callbacks,
    )
    job.parameters = {"ids": [95465499, 30000142]}
    return job
