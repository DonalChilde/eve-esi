"""Cli download and manipulation of schema

TODO option to parse schema for versioned routes?
TODO option to save multiple copies of schema, allow for choice
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Dict

import click
from pfmsoft.aiohttp_queue import AiohttpQueueWorkerFactory
from pfmsoft.aiohttp_queue.runners import queue_runner

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.app_data import save_json_to_app_data
from eve_esi_jobs.esi_provider import get_schema
from eve_esi_jobs.pfmsoft.util.file.read_write import load_json


@click.group()
def schema():
    pass


@click.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["download", "file"], case_sensitive=False),
    default="download",
    show_default=True,
)
@click.option(
    "--destination",
    "-d",
    type=click.Choice(["app-dir", "stdout"], case_sensitive=False),
    default="app-dir",
    show_default=True,
)
@click.option("--source-url")
def get(source, destination, source_url):
    """Get an ESI schema from online or a local file, then save it to the App Data folder or output it to stdout"""

    if source == "download":
        schema_ = download_schema()
    if source == "file":
        if source_url is None:
            click.ClickException(
                "You must provide a source-url when loading from a file."
            )
        try:
            source_path: Path = Path(source_url)
            schema_ = load_json(source_path)
        except Exception as ex:
            raise click.ClickException(
                f"Unable to load file from {source_url} with error message: {ex}"
            )
    if schema_ is None:
        raise click.ClickException("Error loading schema.")
    if destination == "app-dir":
        version = schema_["info"]["version"]
        params = {"version": version}
        file_path = save_json_to_app_data(schema_, "schema", params)
        click.echo(f"Schema saved to {file_path}")
    if destination == "stdout":
        # rich console overflow not compat with pipe to file.
        print(json.dumps(schema_, indent=2))


# @click.command()
# @click.pass_context
# def test(ctx):
#     esi_provider = ctx.obj["esi_provider"]

#     print(json.dumps(esi_provider.op_id_lookup, indent=2))


schema.add_command(get)
# schema.add_command(test)


def download_schema() -> Dict[Any, Any]:
    # where to put this? esi_provider? collection later defined?
    action = get_schema()
    worker = AiohttpQueueWorkerFactory()
    asyncio.run(queue_runner([action], [worker]))
    return action.result
