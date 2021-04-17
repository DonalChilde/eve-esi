from typing import List

from eve_esi_jobs import models
from eve_esi_jobs.eve_esi_jobs import deserialize_job_from_dict

example_1 = {
    "name": "",
    "id_": "",
    "op_id": "example_1",
    "max_attempts": 5,
    "parameters": {},
    "callbacks": {
        "success": [
            {"callback_id": "response_content_to_json"},
            {
                "callback_id": "save_json_result_to_file",
                "kwargs": {"file_path": "data/example_1.json"},
            },
        ]
    },
}


def get_industry_facilities() -> models.EsiJob:
    job_dict = {
        "name": "",
        "id_": "",
        "op_id": "get_industry_facilities",
        "max_attempts": 5,
        "parameters": {},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json"},
                {
                    "callback_id": "save_json_result_to_file",
                    "kwargs": {"file_path": "data/industry-facilities.json"},
                },
            ]
        },
    }
    job = deserialize_job_from_dict(job_dict)
    return job


def get_industry_systems() -> models.EsiJob:
    job_dict = {
        "name": "",
        "id_": "",
        "op_id": "get_industry_systems",
        "max_attempts": 5,
        "parameters": {},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json"},
                {
                    "callback_id": "save_json_result_to_file",
                    "kwargs": {"file_path": "data/industry-systems.json"},
                },
            ]
        },
    }
    job = deserialize_job_from_dict(job_dict)
    return job


def get_markets_region_id_types(region_id: int) -> models.EsiJob:
    job_dict = {
        "name": "",
        "id_": "",
        "op_id": "get_markets_region_id_types",
        "max_attempts": 5,
        "parameters": {"region_id": region_id},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json"},
                {
                    "callback_id": "save_json_result_to_file",
                    "kwargs": {"file_path": "data/markets-${region_id}-types.json"},
                },
            ]
        },
    }
    job = deserialize_job_from_dict(job_dict)
    return job


def post_universe_names(type_ids: List[int]) -> models.EsiJob:
    # need to chunk lists - 1000 max? get from schema
    job_dict = {
        "name": "",
        "id_": "",
        "op_id": "post_universe_names",
        "max_attempts": 5,
        "parameters": {"data": type_ids},
        "callbacks": {
            "success": [
                {"callback_id": "response_content_to_json"},
                {
                    "callback_id": "save_json_result_to_file",
                    "kwargs": {"file_path": "data/names-${esi_job_uid}.json"},
                },
            ]
        },
    }
    job = deserialize_job_from_dict(job_dict)
    return job
