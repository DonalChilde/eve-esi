import json
from pathlib import Path
from string import Template
from typing import Dict

import pytest
import typer
from rich import inspect
from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.eve_esi_jobs import do_work_order
from eve_esi_jobs.helpers import combine_dictionaries
from eve_esi_jobs.models import CallbackCollection, EsiJob, EsiWorkOrder, JobCallback
from eve_esi_jobs.typer_cli import create
from eve_esi_jobs.typer_cli.eve_esi_cli import app

# TODO load jobs from result directories, and validate
# validate workorder functions


def test_create():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "Welcome to Eve Esi Jobs" in result.output
    help_result = runner.invoke(app, ["jobs", "create", "from-op-id", "--help"])
    assert help_result.exit_code == 0
    assert "eve-esi jobs create from-op-id [OPTIONS] OP_ID" in help_result.output


def test_create_job(esi_provider):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    callback_config = ""
    job: EsiJob = create.create_job(op_id, parameters, callback_config, esi_provider)
    assert job.op_id == op_id


def test_decode_param_string():
    # good string
    good_params = {"region_id": 34}
    good_param_string = json.dumps(good_params)
    decoded_string = create.decode_param_string(good_param_string)
    assert decoded_string == good_params

    # bad string
    bad_param_string = good_param_string + "bad"
    with pytest.raises(typer.BadParameter) as ex:
        decoded_string = create.decode_param_string(bad_param_string)
    assert "is not a valid json string" in str(ex.value)

    # None
    result = create.decode_param_string(None)
    assert isinstance(result, dict)


def test_get_params_from_file(sample_data: Dict[str, FileResource]):
    # Not a list of dicts
    not_list_path = sample_data["json-dict.json"].file_path
    with pytest.raises(typer.BadParameter) as ex:
        _ = create.get_params_from_file(not_list_path)
    assert "is not a list of dicts" in str(ex.value)

    # empty list
    empty_list_path = sample_data["empty-list.json"].file_path
    with pytest.raises(typer.BadParameter) as ex:
        _ = create.get_params_from_file(empty_list_path)
    assert "had no data" in str(ex.value)

    # csv
    csv_path = sample_data["3-type-ids.csv"].file_path
    data_from_csv = create.get_params_from_file(csv_path)
    assert len(data_from_csv)
    assert isinstance(data_from_csv, list)
    assert isinstance(data_from_csv[0], dict)

    # json
    json_path = sample_data["3-type-ids.json"].file_path
    data_from_json = create.get_params_from_file(json_path)
    assert len(data_from_json)
    assert isinstance(data_from_json, list)
    assert isinstance(data_from_json[0], dict)

    # None
    result = create.get_params_from_file(None)
    assert result is None


# def test_check_for_callbacks():
#     callback_json = {
#         "success": [
#             {"callback_id": "result_to_json"},
#             {"callback_id": "response_to_esi_job"},
#             {
#                 "callback_id": "save_json_to_file",
#                 "config": {
#                     "file_path_template": "data/market-history/${region_id}-${type_id}.json"
#                 },
#             },
#         ]
#     }
#     callback_string = json.dumps(callback_json)
#     callback_collection = create.check_for_callbacks(callback_string)
#     assert isinstance(callback_collection, CallbackCollection)

#     # bad parameters
#     bad_json = {"success_bad": [{"callback_id": "result_to_json"}]}
#     callback_string_bad_json = json.dumps(bad_json)
#     with pytest.raises(typer.BadParameter) as ex:
#         callback_collection = create.check_for_callbacks(callback_string_bad_json)
#     inspect(ex)
#     assert "ValidationError" in str(ex.value)

#     # malformed string
#     json_data = {"success": [{"callback_id": "result_to_json"}]}
#     callback_string_malformed = json.dumps(json_data)
#     callback_string_malformed = callback_string_malformed + "bad"
#     with pytest.raises(typer.BadParameter) as ex:
#         callback_collection = create.check_for_callbacks(callback_string_malformed)
#     inspect(ex)
#     assert "JSONDecodeError" in str(ex.value)

#     # None
#     result = create.check_for_callbacks(None)
#     assert result is None


def test_default_file_path(esi_provider, test_app_dir):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    callbacks = create.EveEsiDefaultCallbacks().default_callback_collection()
    default_template = "job_data/${esi_job_op_id}-${esi_job_uid}.json"
    template = Template(default_template)
    job: EsiJob = create.create_job(op_id, parameters, callbacks, esi_provider)
    work_order = EsiWorkOrder(parent_path_template=str(test_app_dir))

    work_order.jobs.append(job)
    inspect(work_order)
    expected_path: Path = test_app_dir / Path(template.substitute(job.attributes()))
    do_work_order(work_order, esi_provider)
    assert expected_path.is_file()
    assert expected_path.stat().st_size > 10


def test_check_required_parameters(esi_provider):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    assert create.check_required_params(op_id, parameters, esi_provider)

    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "Fake_param": 34}
    assert create.check_required_params(op_id, parameters, esi_provider) is False


def test_filter_params(esi_provider):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    filtered_params = create.filter_extra_params(op_id, parameters, esi_provider)
    for key in parameters:
        assert key in filtered_params

    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    extra_param = {"param1": 34, "param2": 10}
    combined_params = combine_dictionaries(parameters, [extra_param])
    filtered_params = create.filter_extra_params(op_id, combined_params, esi_provider)
    for key in parameters:
        assert key in filtered_params
    for key in extra_param:
        assert key not in filtered_params


def test_from_op_id_save_created_job(test_app_dir: Path, esi_schema: FileResource):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    output_path = test_app_dir / Path("test_from_op_id_save_created_job")
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-p",
            json.dumps(parameters),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 1
    for file in json_files:
        assert file.stat().st_size > 10


# def test_from_op_id_custom_callback(test_app_dir: Path, esi_schema: FileResource):
#     runner = CliRunner()
#     op_id = "get_markets_region_id_history"
#     parameters = {"region_id": 10000002, "type_id": 34}
#     output_path = test_app_dir / Path("test_from_op_id_custom_callback")
#     callbacks = CallbackCollection()
#     callbacks.success.append(JobCallback(callback_id="response_content_to_json"))
#     callbacks.success.append(
#         JobCallback(
#             callback_id="save_json_result_to_file",
#             kwargs={
#                 "file_path": "job_data_custom/${esi_job_op_id}-${esi_job_uid}.json"
#             },
#         )
#     )
#     callback_string = callbacks.json()
#     result = runner.invoke(
#         app,
#         [
#             "-s",
#             str(esi_schema.file_path),
#             "jobs",
#             "create",
#             "from-op-id",
#             op_id,
#             "-p",
#             json.dumps(parameters),
#             "-c",
#             callback_string,
#             "-o",
#             str(output_path),
#         ],
#         catch_exceptions=False,
#     )
#     assert result.exit_code == 0
#     sub_dir = output_path / Path("created-jobs")
#     json_files = list(sub_dir.glob("*.json"))
#     assert len(json_files) == 1
#     for file in json_files:
#         assert file.stat().st_size > 10

#     # Bad json string
#     callback_string_bad = callback_string + "bad_data"
#     output_path = test_app_dir / Path("test_from_op_id_custom_callback_fail")
#     bad_result = runner.invoke(
#         app,
#         [
#             "-s",
#             str(esi_schema.file_path),
#             "jobs",
#             "create",
#             "from-op-id",
#             op_id,
#             "-p",
#             json.dumps(parameters),
#             "-c",
#             callback_string_bad,
#             "-o",
#             str(test_app_dir),
#         ],
#         catch_exceptions=False,
#     )

#     assert bad_result.exit_code == 2
#     sub_dir = output_path / Path("created-jobs")
#     json_files = list(sub_dir.glob("*.json"))
#     assert len(json_files) == 0
#     for file in json_files:
#         assert file.stat().st_size > 10


def test_from_op_id_path_in_full_data(
    test_app_dir: Path, esi_schema: FileResource, sample_data: Dict[str, FileResource]
):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    output_path = test_app_dir / Path("test_from_op_id_path_in_full_data")
    path_in = sample_data["3-market-history-params.csv"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-i",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 3
    for file in json_files:
        assert file.stat().st_size > 10


def test_from_op_id_path_in_partial_data(
    test_app_dir: Path, esi_schema: FileResource, sample_data: Dict[str, FileResource]
):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002}
    output_path = test_app_dir / Path("test_from_op_id_path_in_partial_data")
    path_in = sample_data["3-type-ids.json"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-p",
            json.dumps(parameters),
            "-i",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 3
    for file in json_files:
        assert file.stat().st_size > 10


def test_from_op_id_path_in_extra_data(
    test_app_dir: Path, esi_schema: FileResource, sample_data: Dict[str, FileResource]
):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002}
    output_path = test_app_dir / Path("test_from_op_id_path_in_extra_data")
    path_in = sample_data["3-market-history-params-extras.json"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-p",
            json.dumps(parameters),
            "-i",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 3
    for file in json_files:
        assert file.stat().st_size > 10


def test_from_op_id_path_in_bad_data(
    test_app_dir: Path, esi_schema: FileResource, sample_data: Dict[str, FileResource]
):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002}
    output_path = test_app_dir / Path("test_from_op_id_path_in_bad_data")
    path_in = sample_data["3-wrong-params.json"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-p",
            json.dumps(parameters),
            "-i",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 2
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 0
    for file in json_files:
        assert file.stat().st_size > 10


def test_load_json_or_csv(sample_data: Dict[str, FileResource]):
    json_resource = sample_data["3-market-history-params.json"]
    json_data = create.load_json_or_csv(json_resource.file_path)
    assert json_data == json.loads(json_resource.data)

    csv_resource = sample_data["3-market-history-params.csv"]
    json_from_csv_data = create.load_json_or_csv(csv_resource.file_path)
    assert len(json_from_csv_data) == 3


def test_data_from_csv(
    sample_data: Dict[str, FileResource], esi_schema, test_app_dir: Path
):
    # FIXME use callback json file
    file_resource = sample_data["3-market-history-params.csv"]
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    callbacks = CallbackCollection()
    callbacks.success.append(JobCallback(callback_id="response_content_to_json"))
    callbacks.success.append(
        JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={
                "file_path": "job_data_custom/${esi_job_op_id}-${esi_job_uid}.json"
            },
        )
    )
    callback_string = callbacks.json()
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "jobs",
            op_id,
            "-p",
            json.dumps(parameters),
            "-i",
            str(file_resource.file_path),
            "-c",
            callback_string,
            "-o",
            str(test_app_dir),
        ],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
