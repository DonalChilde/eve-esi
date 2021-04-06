from pathlib import Path
from typing import Dict

import pytest
from tests.eve_esi_jobs.conftest import FileResource
from typer.testing import CliRunner

from eve_esi_jobs.typer_cli.eve_esi_cli import app


@pytest.fixture(scope="module")
def collect_jobs_test_data(
    test_app_dir: Path, esi_schema: FileResource, sample_data: Dict[str, FileResource]
):
    runner = CliRunner()
    op_id = "get_markets_region_id_history"
    output_path = test_app_dir / Path("collect_jobs_test_data")
    path_in = sample_data["3-market-history-params.csv"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "jobs",
            "create",
            "from-op-id",
            op_id,
            "-i",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    print(result.stdout)
    assert result.exit_code == 0

    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 3
    for file in json_files:
        assert file.stat().st_size > 10


def test_data(test_app_dir, collect_jobs_test_data):
    output_path = test_app_dir / Path("collect_jobs_test_data")
    sub_dir = output_path / Path("created-jobs")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 3
    for file in json_files:
        assert file.stat().st_size > 10


def test_collect_jobs(test_app_dir, collect_jobs_test_data, esi_schema):
    runner = CliRunner()
    output_path = test_app_dir / Path(
        "collect_jobs_test_result/workorder-${ewo_iso_date_time}-${ewo_uid}.json"
    )
    path_in = test_app_dir / Path("collect_jobs_test_data") / Path("created-jobs")
    # path_in = sample_data["3-market-history-params.csv"].file_path
    result = runner.invoke(
        app,
        [
            "-s",
            str(esi_schema.file_path),
            "jobs",
            "collect",
            "jobs",
            str(path_in),
            "-o",
            str(output_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    sub_dir = test_app_dir / Path("collect_jobs_test_result")
    json_files = list(sub_dir.glob("*.json"))
    assert len(json_files) == 1
    for file in json_files:
        assert file.stat().st_size > 10


def test_load_job():
    pass