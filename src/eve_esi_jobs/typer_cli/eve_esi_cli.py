"""Main entry for eve-esi"""

# TODO silent flag to support stdout pipe to file

import logging
from time import perf_counter_ns

import typer

from eve_esi_jobs.app_data import load_schema
from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.typer_cli.jobs import app as jobs_app
from eve_esi_jobs.typer_cli.schema import app as schema_app

app = typer.Typer()
app.add_typer(jobs_app, name="jobs")
app.add_typer(schema_app, name="schema")
logger = logging.getLogger(__name__)


@app.callback()
def eve_esi_main(
    ctx: typer.Context,
    version: str = typer.Option(
        "latest",
        "--version",
        help="schema version to load from Eve Esi Jobs app data directory",
    ),
    schema_path: str = typer.Option(None, "-s", help="path to local schema"),
):
    """
    Welcome to Eve Esi Jobs. Try one of the commands below.


    """
    # TODO load schema from file
    # TODO fix flow when no schema
    ctx.obj = {}
    start = perf_counter_ns()
    ctx.obj["start_time"] = start
    schema = load_schema(version)
    if schema is None:
        typer.echo(
            (
                "ESI schema was not found. Use `eve-esi schema get` to download "
                "the schema, or provide a valid local path to the schema."
            )
        )
    try:
        esi_provider = EsiProvider(schema)
    except Exception:
        # TODO beter exception selection
        logger.exception(
            "Tried to make esi_provider with invalid schema. version: %s, file_path: %s",
            version,
            schema_path,
        )
        raise typer.BadParameter(
            "The provided schema was invalid. please try a different one."
        )
    ctx.obj["esi_provider"] = esi_provider
    typer.echo(
        f"Loaded ESI schema version {esi_provider.schema_version()} from app data\n"
    )


if __name__ == "__main__":
    app()
