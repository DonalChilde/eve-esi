from pathlib import Path
from typing import Dict, List

from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.eve_esi_jobs import deserialize_work_order_from_string
from eve_esi_jobs.typer_cli.eve_esi_cli import app


def test_create_workorder(test_app_dir, jobs: Dict[str, FileResource], esi_schema):
    runner = CliRunner()
    output_path = test_app_dir / Path("create_workorder_test_result/")
    keys = list(jobs.keys())
    path_in = jobs[keys[0]].file_path.parent
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "create",
            "ewo",
            str(path_in),
            str(output_path),
        ],
        catch_exceptions=False,
    )
    print(result.output)
    assert result.exit_code == 0
    sub_dir = test_app_dir / Path("create_workorder_test_result")
    # NOTE: Expects to find only one workorder json file in sub directories.
    json_files: List[Path] = list(sub_dir.glob("**/*.json"))
    assert len(json_files) == 1
    for file in json_files:
        assert file.stat().st_size > 10
        workorder_string = file.read_text()
        workorder = deserialize_work_order_from_string(workorder_string)
        assert len(workorder.jobs) == 3
    # assert False


# def test_load_job():
#     pass
