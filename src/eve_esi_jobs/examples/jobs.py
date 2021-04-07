from eve_esi_jobs import models


def get_industry_facilities():
    job = models.EsiJob(op_id="get_industry_facilities", name="get_industry_facilities")
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-facilities.json"},
        )
    )
    return job


def get_industry_systems():
    job = models.EsiJob(op_id="get_industry_systems", name="get_industry_systems")
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-systems.json"},
        )
    )
    return job


def post_universe_names():
    job = models.EsiJob(op_id="post_universe_names", name="post_universe_names")
    job.parameters = {"ids": [95465499, 30000142]}
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/post_universe_names-${esi_job_uid}.json"},
        )
    )
    return job
