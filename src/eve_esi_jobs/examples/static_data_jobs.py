from eve_esi_jobs import models


def get_industry_facilities():
    job = models.EsiJob(
        op_id="get_industry_facilities",
    )
    job.result_callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.result_callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-facilities.json"},
        )
    )
    return job


def get_industry_systems():
    job = models.EsiJob(
        op_id="get_industry_systems",
    )
    job.result_callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.result_callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path": "data/industry-systems.json"},
        )
    )
    return job
