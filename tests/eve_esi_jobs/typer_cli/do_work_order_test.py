import os
from pathlib import Path
from typing import Dict, List

import pytest
from rich import inspect
from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.typer_cli.eve_esi_cli import app

# def test_command_line_interface():
#     """Test the CLI."""
#     runner = CliRunner()
#     result = runner.invoke(app)
#     assert result.exit_code == 0
#     assert "Welcome to Eve Esi Jobs" in result.output
#     help_result = runner.invoke(app, ["--help"])
#     assert help_result.exit_code == 0
#     assert "[OPTIONS] COMMAND [ARGS]" in help_result.output


def test_do_ewo_help(esi_schema):
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "ewo", "--help"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Usage: eve-esi do ewo [OPTIONS] PATH_IN [PATH_OUT]" in result.output


def test_do_job_help(esi_schema):
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "job", "--help"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Usage: eve-esi do job [OPTIONS] PATH_IN [PATH_OUT]" in result.output


def test_do_job(esi_schema, jobs: Dict[str, FileResource], test_app_dir: Path):
    runner = CliRunner()
    job_path = jobs["get_industry_facilities.json"].file_path
    output_path = test_app_dir / Path("test-do-job")
    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "job", str(job_path), str(output_path)],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
    json_files: List[Path] = list(output_path.glob("**/*.json"))
    assert len(json_files) == 2
    for file in json_files:
        assert file.stat().st_size > 10


def test_do_example_workorder(
    esi_schema, work_orders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = work_orders["example_workorder.json"].file_path
    output_path = test_app_dir / Path("test_do_example_workorder")
    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "ewo", str(ewo_path), str(output_path)],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
    json_files: List[Path] = list(output_path.glob("**/*.json"))
    assert len(json_files) == 5
    for file in json_files:
        assert file.stat().st_size > 10
    assert "Uncertain Result" not in result.output
    assert "Failed" not in result.output


def test_do_bad_validation_workorder(
    esi_schema, bad_work_orders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = bad_work_orders["bad-validation-workorder.json"].file_path
    output_path = test_app_dir / Path("test_do_bad-validation-workorder")
    with pytest.raises(ValueError):
        result = runner.invoke(
            app,
            [
                "-s",
                str(esi_schema.file_path),
                "do",
                "ewo",
                str(ewo_path),
                str(output_path),
            ],
            catch_exceptions=False,
        )


def test_do_bad_status_workorder(
    esi_schema, bad_work_orders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = bad_work_orders["bad-status-workorder.json"].file_path
    output_path = test_app_dir / Path("test_do_bad-status-workorder")

    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "ewo", str(ewo_path), str(output_path)],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
    json_files: List[Path] = list(output_path.glob("**/*.json"))
    assert len(json_files) == 0
    for file in json_files:
        assert file.stat().st_size > 10
    assert "Uncertain Result" not in result.output
    assert "Failed" in result.output


# def test_create_workorder(test_app_dir, jobs: Dict[str, FileResource], esi_schema):
#     runner = CliRunner()
#     output_path = test_app_dir / Path("create_workorder_test_result/")
#     keys = list(jobs.keys())
#     path_in = jobs[keys[0]].file_path.parent
#     result = runner.invoke(
#         app,
#         [
#             "-s",
#             str(esi_schema.file_path),
#             "create",
#             "ewo",
#             str(path_in),
#             str(output_path),
#         ],
#         catch_exceptions=False,
#     )
#     # print(result.output)
#     assert result.exit_code == 0
#     sub_dir = test_app_dir / Path("create_workorder_test_result")
#     # NOTE: Expects to find only one workorder json file in sub directories.
#     json_files: List[Path] = list(sub_dir.glob("**/*.json"))
#     assert len(json_files) == 1
#     for file in json_files:
#         assert file.stat().st_size > 10
#         workorder_string = file.read_text()
#         workorder = deserialize_work_order_from_string(workorder_string)
#         assert len(workorder.jobs) == 3
#         yaml_string = pydantic_model_to_yaml_string(workorder)
#         print(yaml_string)
#         workorder_yaml = yaml_string_to_pydantic_model(yaml_string, EsiWorkOrder)
#         assert len(workorder_yaml.jobs) == 3
#         assert workorder == workorder_yaml
#     # assert False
