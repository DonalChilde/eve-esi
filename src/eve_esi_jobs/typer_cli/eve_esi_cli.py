"""Main entry for eve-esi"""

# TODO silent flag to support stdout pipe to file

import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Optional

import typer

# from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.operation_manifest import OperationManifest
from eve_esi_jobs.typer_cli.app_config import make_config_from_env
from eve_esi_jobs.typer_cli.app_data import load_schema
from eve_esi_jobs.typer_cli.create import app as create_app
from eve_esi_jobs.typer_cli.do_work_order import app as do_app
from eve_esi_jobs.typer_cli.examples import app as examples_app
from eve_esi_jobs.typer_cli.schema import app as schema_app
from eve_esi_jobs.typer_cli.schema import download_json

app = typer.Typer()
app.add_typer(do_app, name="do")
app.add_typer(schema_app, name="schema")
app.add_typer(create_app, name="create")
app.add_typer(examples_app, name="examples")

logger = logging.getLogger(__name__)


@app.callback()
def eve_esi(
    ctx: typer.Context,
    version: str = typer.Option(
        "latest",
        "--version",
        help="Esi schema version to load from Eve Esi Jobs app data directory",
    ),
    schema_path: Optional[Path] = typer.Option(
        None, "--schema-path", "-s", help="Path to local schema file."
    ),
):
    """
    Welcome to Eve Esi Jobs. Get started by downloading a schema, or checkout the
    docs at: https://eve-esi-jobs.readthedocs.io/en/latest/
    """
    config = make_config_from_env()
    typer.echo(f"Logging at {config.log_path}")
    ctx.obj = {}
    start = perf_counter_ns()
    ctx.obj["start_time"] = start
    logger.info("loading schema")
    ctx.obj["config"] = config
    schema = None
    schema_source = ""
    if schema_path is not None:
        try:
            schema_text = schema_path.read_text()
            schema = json.loads(schema_text)
            typer.echo(f"Loaded schema from {schema_path}")
            schema_source = str(schema_path)
        except FileNotFoundError as ex:
            logger.exception("Error loading schema from file.")
            raise typer.BadParameter(
                f"Error loading schema from {schema_path}. "
                f"Error: {ex.__class__.__name__} msg: {ex}."
            )
    else:
        schema = load_schema(config.app_dir, version)
        schema_source = str(config.app_dir) + f"version: {version}"
        if schema is None:
            typer.echo("Schema not found in app data, attempting to download.")
            typer.echo("Consider using `eve-esi schema download` to save a local copy,")
            typer.echo("or provide a valid local path to the schema.")
            schema = download_json(config.schema_url)
            schema_source = config.schema_url
    try:
        operation_manifest = OperationManifest(schema)
    except Exception as ex:
        logger.exception(
            "Tried to make operation_manifest with invalid schema. version: %s, source: %s, error: %s, msg: %s",
            version,
            schema_source,
            ex.__class__.__name__,
            ex,
        )
        raise typer.BadParameter(
            "The provided schema was invalid. please try a different one."
        )
    ctx.obj["operation_manifest"] = operation_manifest
    typer.echo(f"Loaded ESI schema version {operation_manifest.version}.\n")


if __name__ == "__main__":
    app()
