import logging

from eve_esi_jobs.models import CallbackCollection, JobCallback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def default_callback_collection() -> CallbackCollection:
    callback_collection = CallbackCollection()
    callback_collection.success.append(
        JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.fail.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.fail.append(JobCallback(callback_id="log_job_failure"))
    return callback_collection
