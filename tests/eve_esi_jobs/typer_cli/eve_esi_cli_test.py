import os

from rich import inspect
from typer.testing import CliRunner

from eve_esi_jobs.typer_cli.eve_esi_cli import app


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "Welcome to Eve Esi Jobs" in result.output
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "[OPTIONS] COMMAND [ARGS]" in help_result.output


def test_env_settings():
    testing = os.getenv("PFMSOFT_eve_esi_jobs_TESTING", "Not Set")
    assert testing == "True"


def test_load_schema_from_file(esi_schema, monkeypatch):
    # Load from file
    runner = CliRunner()
    result = runner.invoke(app, ["-s", esi_schema.file_path, "schema"])
    inspect(result)
    assert result.exit_code == 0
    assert f"Loaded schema from {esi_schema.file_path}" in result.output

    # Fail to load from file
    runner = CliRunner()
    result = runner.invoke(app, ["-s", "foo", "schema"])
    inspect(result)
    assert result.exit_code == 2
    assert "foo is not a valid file path." in result.output

    # Bad schema

    # Fail to load from app data
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_APP_DIR", "tmp")
    runner = CliRunner()
    result = runner.invoke(app, ["schema"])
    inspect(result)
    assert result.exit_code == 0
    assert "Schema not found in app data" in result.output


def test_load_schema_from_app_data(monkeypatch):
    """expects to find schema in real app_data

    May not work with travis
    """
    # Load from app data
    monkeypatch.delenv("PFMSOFT_eve_esi_jobs_APP_DIR")
    runner = CliRunner()
    result = runner.invoke(app, ["schema"])
    inspect(result)
    assert result.exit_code == 0
    assert "Loaded ESI schema version" in result.output
