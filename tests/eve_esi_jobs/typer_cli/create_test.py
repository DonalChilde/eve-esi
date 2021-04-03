import json
from pathlib import Path
from string import Template

from rich import inspect
from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.eve_esi_jobs import do_work_order
from eve_esi_jobs.helpers import combine_dictionaries
from eve_esi_jobs.models import CallbackCollection, EsiJob, EsiWorkOrder, JobCallback
from eve_esi_jobs.typer_cli import create
from eve_esi_jobs.typer_cli.eve_esi_cli import app


def test_create():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "Welcome to Eve Esi Jobs" in result.output
    help_result = runner.invoke(app, ["create", "from-op-id", "--help"])
    assert help_result.exit_code == 0
    assert "eve-esi create from-op-id [OPTIONS] OP_ID" in help_result.output


def test_create_job(esi_provider):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    callback_config = ""
    job: EsiJob = create.create_job(op_id, parameters, callback_config, esi_provider)
    assert job.op_id == op_id


def test_default_file_path(esi_provider, test_app_dir):
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    callback_config = None
    default_template = "job_data/${esi_job_op_id}-${esi_job_uid}.json"
    template = Template(default_template)
    job: EsiJob = create.create_job(op_id, parameters, callback_config, esi_provider)
    work_order = EsiWorkOrder(parent_path_template=str(test_app_dir))

    work_order.jobs.append(job)
    inspect(work_order)
    expected_path: Path = test_app_dir / Path(
        template.substitute(job.get_template_overrides())
    )
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


def test_from_op_id_save_created_job(test_app_dir, esi_schema: FileResource):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    parameters = {"region_id": 10000002, "type_id": 34}
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "from-op-id",
            op_id,
            "-p",
            json.dumps(parameters),
            "-o",
            test_app_dir,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    # Job uuid is created at run time, figure out a way to confirm
    # job was saved?


def test_from_op_id_custom_callback(test_app_dir, esi_schema: FileResource):
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
            "from-op-id",
            op_id,
            "-p",
            json.dumps(parameters),
            "-c",
            callback_string,
            "-o",
            test_app_dir,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Bad json string
    callback_string_bad = callback_string + "bad_data"
    bad_result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "from-op-id",
            op_id,
            "-p",
            json.dumps(parameters),
            "-c",
            callback_string_bad,
            "-o",
            test_app_dir,
        ],
        catch_exceptions=False,
    )
    # print(bad_result.output)
    assert bad_result.exit_code == 2


def test_load_json_or_csv():
    pass
