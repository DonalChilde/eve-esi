"""Examples of job building methods, for use in building jinja templates."""
from eve_esi_jobs import models


def get_industry_facilities():
    job = models.EsiJob(
        op_id="get_industry_facilities",
    )
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path_template": "data/industry-facilities.json"},
        )
    )
    return job


def get_industry_systems():
    job = models.EsiJob(
        op_id="get_industry_systems",
    )
    job.callbacks.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    job.callbacks.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path_template": "data/industry-systems.json"},
        )
    )
    return job
