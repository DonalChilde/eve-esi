"""These tests are not meant to be run during normal testing.

Uncomment the tests below to update test resources.
"""
import json
from pathlib import Path

import yaml

from eve_esi_jobs import models
from eve_esi_jobs.typer_cli.examples import (  # save_callback_examples,
    save_input_data_examples,
    save_job_examples,
    save_work_order_examples,
)

REFRESH_RESOURCES = False


def test_job_examples():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    data_path = save_job_examples(parent_path)
    init = data_path / Path("__init__.py")
    init.touch()


def test_ewo_examples():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    data_path = save_work_order_examples(parent_path)
    init = data_path / Path("__init__.py")
    init.touch()


# def test_callback_collections():
#     if not REFRESH_RESOURCES:
#         assert True
#         return
#     parent_path = Path(__file__).parent
#     data_path = save_callback_examples(parent_path)
#     init = data_path / Path("__init__.py")
#     init.touch()


def test_save_input_data_examples():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    data_path = save_input_data_examples(parent_path)
    init = data_path / Path("__init__.py")
    init.touch()


def test_bad_workorders():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("bad-workorders")
    output_path.mkdir(parents=True, exist_ok=True)
    init = output_path / Path("__init__.py")
    init.touch()
    ewo_list = [bad_status_workorder, bad_validation_workorder]
    for item in ewo_list:
        ewo: models.EsiWorkOrder = item()
        file_path = output_path / Path(ewo.name)
        json_path = file_path.with_suffix(".json")
        json_path.write_text(ewo.serialize_json())
        yaml_path = file_path.with_suffix(".yaml")
        yaml_path.write_text(ewo.serialize_yaml())


def test_bad_jobs():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("bad-jobs")
    output_path.mkdir(parents=True, exist_ok=True)
    init = output_path / Path("__init__.py")
    init.touch()
    jobs_list = [bad_parameter_job, missing_parameter_job]
    for sample in jobs_list:
        job: models.EsiJob = sample()
        file_path = output_path / Path(job.name)
        json_path = file_path.with_suffix(".json")
        json_path.write_text(job.serialize_json())
        yaml_path = file_path.with_suffix(".yaml")
        yaml_path.write_text(job.serialize_yaml())


def test_bad_data():
    if not REFRESH_RESOURCES:
        assert True
        return
    parent_path = Path(__file__).parent
    output_path = parent_path / Path("bad-data")
    output_path.mkdir(parents=True, exist_ok=True)
    init = output_path / Path("__init__.py")
    init.touch()
    dict_not_list = {"region_id": 10000002, "type_id": 34}
    json_path = output_path / Path("dict_not_list").with_suffix(".json")
    json_path.write_text(json.dumps(dict_not_list, indent=2))
    yaml_path = json_path.with_suffix(".yaml")
    yaml_path.write_text(yaml.dump(dict_not_list, sort_keys=False))
    wrong_params = {"apple": "red", "pear": "yellow", "orange": 42}
    json_path = output_path / Path("wrong_params").with_suffix(".json")
    json_path.write_text(json.dumps(wrong_params, indent=2))
    yaml_path = json_path.with_suffix(".yaml")
    yaml_path.write_text(yaml.dump(wrong_params, sort_keys=False))
    empty_list = []
    json_path = output_path / Path("empty_list").with_suffix(".json")
    json_path.write_text(json.dumps(empty_list, indent=2))
    yaml_path = json_path.with_suffix(".yaml")
    yaml_path.write_text(yaml.dump(empty_list, sort_keys=False))


def bad_status_workorder():
    ewo = models.EsiWorkOrder(
        name="bad-status-workorder",
        description=(
            "A workorder that contains jobs that will fail on the server "
            "in various ways."
        ),
        id_="bad-status-workorder",
        output_path="samples/workorder_output/${ewo_name}",
    )
    ewo.jobs.append(bad_parameter_job())
    return ewo


def bad_validation_workorder():
    ewo = models.EsiWorkOrder(
        name="bad-validation-workorder",
        description="A workorder that contains jobs that will fail validation.",
        id_="bad-validation-workorder",
        output_path="samples/workorder_output/${ewo_name}",
    )
    ewo.jobs.append(missing_parameter_job())
    return ewo


def missing_parameter_job():
    job = models.EsiJob(
        name="missing-parameter",
        description="A job with a missing parameter, should result in a validation failure.",
        id_="missing-parameter",
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002},
        # callbacks=default_callback_collection(),
    )
    return job


def bad_parameter_job():
    job = models.EsiJob(
        name="bad-parameter",
        description="A job with a bad parameter, should result in a 400 bad request.",
        id_="bad-parameter",
        op_id="get_markets_region_id_history",
        parameters={"region_id": 10000002, "type_id": 0},
        # callbacks=default_callback_collection(),
    )
    return job
