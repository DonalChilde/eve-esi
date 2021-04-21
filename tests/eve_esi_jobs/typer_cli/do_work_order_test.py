from pathlib import Path
from typing import Dict, List

import pytest
from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.typer_cli.eve_esi_cli import app


def test_do_ewo_help(esi_schema):
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["-s", str(esi_schema.file_path), "do", "workorder", "--help"],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
    assert "Usage: eve-esi do workorder [OPTIONS] PATH_IN [PATH_OUT]" in result.output


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
    esi_schema, workorders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = workorders["example_workorder.json"].file_path
    output_path = test_app_dir / Path("test_do_example_workorder")
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "do",
            "workorder",
            str(ewo_path),
            str(output_path),
        ],
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
    # assert False


def test_do_bad_validation_workorder(
    esi_schema, bad_workorders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = bad_workorders["bad-validation-workorder.json"].file_path
    output_path = test_app_dir / Path("test-do-bad-validation-workorder")
    with pytest.raises(ValueError):
        result = runner.invoke(
            app,
            [
                "-s",
                str(esi_schema.file_path),
                "do",
                "workorder",
                str(ewo_path),
                str(output_path),
            ],
            catch_exceptions=False,
        )
        _ = result


def test_do_bad_status_workorder(
    esi_schema, bad_workorders: Dict[str, FileResource], test_app_dir: Path
):
    runner = CliRunner()
    ewo_path = bad_workorders["bad-status-workorder.json"].file_path
    output_path = test_app_dir / Path("test_do_bad-status-workorder")

    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "do",
            "workorder",
            str(ewo_path),
            str(output_path),
        ],
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
