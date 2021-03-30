"""Working with ESI schema"""

import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, List, Optional, Union

import typer
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import do_action_runner

from eve_esi_jobs.app_config import SCHEMA_URL
from eve_esi_jobs.app_data import save_json_to_app_data
from eve_esi_jobs.helpers import save_json

logger = logging.getLogger(__name__)
app = typer.Typer(
    help="Download and inspect Esi schemas. use --help on the commands below for more options."
)


@app.command()
def download(
    ctx: typer.Context,
    url: str = typer.Option(SCHEMA_URL, "--url", help="The url to ESI schema."),
    destination: str = typer.Option(
        "app-data",
        "-d",
        help=(
            "Location to output schema. Use stdout to print to console, "
            "and a file path to save to file."
        ),
    ),
):
    """Download a schema, use --help for more options."""
    schema: Optional[Dict] = download_json(url)
    if schema is None:
        typer.BadParameter(f"Unable to download schema from {url}")
    if destination == "app-data":
        version = schema["info"]["version"]
        params = {"version": version}
        file_path = save_json_to_app_data(schema, "schema", params)
        typer.echo(f"Schema saved to {file_path}")
        typer.Exit()
    elif destination == "stdout":
        typer.echo(json.dumps(schema, indent=2))
        typer.Exit()
    else:
        schema_path = Path(destination) / Path("esi_schema.json")
        save_json(schema, schema_path, parents=True)
        typer.echo(f"Schema saved to {schema_path.resolve()}")
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")
    # logger.info(
    #     "%s Actions sequentially completed -  took %s seconds, %s actions per second.",
    #     len(actions),
    #     f"{seconds:9f}",
    #     f"{len(actions)/seconds:1f}",
    # )


def download_json(url):
    """Convenience method for downloading a single url, expecting json"""
    callbacks = ActionCallbacks(success=[ResponseContentToJson()])
    action = AiohttpAction("get", url, callbacks=callbacks)
    do_action_runner([action])
    if action.response.status == 200:
        return action.result
    logger.warning(
        "Failed to download url. url: %s, status: %s, msg: %s",
        action.response.real_url,
        action.response.status,
        action.result,
    )
    return None
