from eve_esi_jobs import models


def no_file_output() -> models.CallbackCollection:
    callback_collection = models.CallbackCollection()
    callback_collection.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.fail.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return callback_collection


def generic_save_result_to_json() -> models.CallbackCollection:
    callback_collection = models.CallbackCollection()
    callback_collection.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.success.append(
        models.JobCallback(
            callback_id="save_result_to_json_file",
            kwargs={
                "file_path_template": "job_data/${esi_job_op_id}-${esi_job_uid}.json"
            },
        )
    )
    callback_collection.fail.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return callback_collection


def generic_save_result_and_job_to_separate_json() -> models.CallbackCollection:
    callback_collection = models.CallbackCollection()
    callback_collection.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.success.append(
        models.JobCallback(
            callback_id="save_result_to_json_file",
            kwargs={
                "file_path_template": "job_data/${esi_job_op_id}-${esi_job_uid}.json"
            },
        )
    )
    callback_collection.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path_template": "job_data/${esi_job_op_id}-${esi_job_uid}.esi-job.json"
            },
        )
    )
    callback_collection.fail.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return callback_collection


def generic_save_result_and_job_to_same_json() -> models.CallbackCollection:
    callback_collection = models.CallbackCollection()
    callback_collection.success.append(
        models.JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.success.append(
        models.JobCallback(callback_id="result_to_esi_job")
    )
    callback_collection.success.append(
        models.JobCallback(
            callback_id="save_esi_job_to_json_file",
            kwargs={
                "file_path_template": "job_data/${esi_job_op_id}-${esi_job_uid}.esi-job.json"
            },
        )
    )
    callback_collection.fail.append(
        models.JobCallback(callback_id="response_to_esi_job")
    )
    callback_collection.fail.append(models.JobCallback(callback_id="log_job_failure"))
    return callback_collection
