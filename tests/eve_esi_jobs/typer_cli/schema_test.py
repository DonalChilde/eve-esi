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
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "Usage: eve-esi schema [OPTIONS] COMMAND [ARGS]" in help_result.output


def test_download():
    runner = CliRunner()
    result = runner.invoke(app, ["schema", "download"])
    print(result.output)
    assert result.exit_code == 0
    assert "Schema saved to" in result.output
    help_result = runner.invoke(app, ["schema", "download", "--help"])
    assert help_result.exit_code == 0
    assert "eve-esi schema download [OPTIONS]" in help_result.output
