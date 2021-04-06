"""Main entry for eve-esi"""

# TODO silent flag to support stdout pipe to file

import logging
from pathlib import Path
from time import perf_counter_ns

import typer

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.typer_cli.app_config import make_config_from_env
from eve_esi_jobs.typer_cli.app_data import load_schema
from eve_esi_jobs.typer_cli.cli_helpers import load_json
from eve_esi_jobs.typer_cli.jobs import app as jobs_app
from eve_esi_jobs.typer_cli.schema import app as schema_app
from eve_esi_jobs.typer_cli.schema import download_json

app = typer.Typer()
app.add_typer(jobs_app, name="jobs")
app.add_typer(schema_app, name="schema")

logger = logging.getLogger(__name__)


@app.callback()
def eve_esi(
    ctx: typer.Context,
    version: str = typer.Option(
        "latest",
        "--version",
        help="schema version to load from Eve Esi Jobs app data directory",
    ),
    schema_path: str = typer.Option(
        None, "--schema-path", "-s", help="path to local schema"
    ),
):
    """
    Welcome to Eve Esi Jobs. Try one of the commands below.
    Checkout the docs at: https://eve-esi-jobs.readthedocs.io/en/latest/


    """
    # TODO fix flow when no schema
    config = make_config_from_env()
    typer.echo(f"Logging at {config.log_path}")
    ctx.obj = {}
    start = perf_counter_ns()
    ctx.obj["start_time"] = start
    logger.info("loading schema")
    ctx.obj["config"] = config
    schema = None
    if schema_path is not None:
        try:
            schema = load_json(Path(schema_path))
            typer.echo(f"Loaded schema from {schema_path}")
        except FileNotFoundError as ex:
            logger.exception("Tried to load schema from file, not found.")
            raise typer.BadParameter(f"{schema_path} is not a valid file path.")
    else:
        schema = load_schema(config.app_dir, version)
        if schema is None:
            typer.echo("Schema not found in app data, attempting to download.")
            typer.echo("Consider using `eve-esi schema download` to save a local copy,")
            typer.echo("or provide a valid local path to the schema.")
            schema = download_json(config.schema_url)
    try:
        esi_provider = EsiProvider(schema)
    except Exception:
        logger.exception(
            "Tried to make esi_provider with invalid schema. version: %s, file_path: %s",
            version,
            schema_path,
        )
        raise typer.BadParameter(
            "The provided schema was invalid. please try a different one."
        )
    ctx.obj["esi_provider"] = esi_provider
    typer.echo(f"Loaded ESI schema version {esi_provider.schema_version}.\n")


if __name__ == "__main__":
    app()
