import logging
import os

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


def test_schema():
    runner = CliRunner()
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert "Usage: eve-esi schema [OPTIONS] COMMAND [ARGS]" in result.output
    help_result = runner.invoke(app, ["schema", "--help"])
    assert help_result.exit_code == 0
    assert "Usage: eve-esi schema [OPTIONS] COMMAND [ARGS]" in help_result.output
    print(os.getenv("PFMSOFT_eve_esi_jobs_TESTING", "Not set"))
    assert False


def test_download(test_app_dir, monkeypatch):
    # set_env(test_app_dir, monkeypatch)
    runner = CliRunner()
    result = runner.invoke(app, ["schema", "download"])
    print(result.output)
    assert result.exit_code == 0
    assert "Schema saved to" in result.output
    help_result = runner.invoke(app, ["schema", "download", "--help"])
    assert help_result.exit_code == 0
    assert "eve-esi schema download [OPTIONS]" in help_result.output
    assert False


def set_env(test_app_dir, monkeypatch):
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_TESTING", "True")
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_LOG_LEVEL", str(logging.INFO))
    monkeypatch.setenv("PFMSOFT_eve_esi_jobs_APP_DIR", str(test_app_dir))
