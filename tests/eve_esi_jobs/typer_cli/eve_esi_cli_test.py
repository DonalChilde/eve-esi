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
    # assert False


def test_env_settings():
    testing = os.getenv("PFMSOFT_eve_esi_jobs_TESTING", "Not Set")
    assert testing == "True"
