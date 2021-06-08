"""Examples of job building methods, for use in building jinja templates."""
from eve_esi_jobs import models


def get_industry_facilities():
    job = models.EsiJob(
        op_id="get_industry_facilities",
    )

    job.callbacks.append(
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

    job.callbacks.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={"file_path_template": "data/industry-systems.json"},
        )
    )
    return job
