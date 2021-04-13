"""Working with ESI schema"""

import dataclasses
import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, List, Optional

import typer
import yaml
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import do_action_runner
from rich import inspect

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.typer_cli.app_config import EveEsiJobConfig

# from eve_esi_jobs.app_config import SCHEMA_URL
from eve_esi_jobs.typer_cli.app_data import save_json_to_app_data
from eve_esi_jobs.typer_cli.cli_helpers import (
    check_for_op_id,
    completion_op_id,
    report_finished_task,
    save_json,
)

logger = logging.getLogger(__name__)
app = typer.Typer(
    help="Download and inspect Esi schemas. use --help on the commands below for more options."
)


# def complete_op_id_3(ctx: typer.Context, incomplete: str):
#     completion = []
#     for name in OPID:
#         if name.startswith(incomplete):
#             completion.append(name)
#     return completion


# def complete_op_id_2(ctx: typer.Context):

#     return OPID


@app.command()
def browse(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ..., autocompletion=completion_op_id, callback=check_for_op_id
    ),
):
    """Browse schema by op_id, use tab for completion."""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        typer.BadParameter(f"Invalid op_id: {op_id}")
    typer.echo(yaml.dump(dataclasses.asdict(op_id_info)))
    report_finished_task(ctx)


@app.command()
def list_op_ids(
    ctx: typer.Context,
    output: str = typer.Argument("list", help="use json for json output"),
):
    """List available op_ids, add json for json output."""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_keys = list(esi_provider.op_id_lookup)
    op_id_keys.sort()
    if output == "json":
        op_ids = json.dumps(op_id_keys, indent=2)
    else:
        op_ids = "\n".join(op_id_keys)
    typer.echo(op_ids)
    report_finished_task(ctx)


@app.command()
def download(
    ctx: typer.Context,
    url: str = typer.Option(
        "https://esi.evetech.net/latest/swagger.json",
        "--url",
        help="The url to ESI schema.",
    ),
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
    config: EveEsiJobConfig = ctx.obj["config"]
    url = config.schema_url
    schema: Optional[Dict] = download_json(url)
    if schema is None:
        typer.BadParameter(f"Unable to download schema from {url}")
    if destination == "app-data":
        # pylint: disable=unsubscriptable-object
        version = schema["info"]["version"]  # type: ignore
        params = {"version": version}
        file_path = save_json_to_app_data(schema, config.app_dir, "schema", params)
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
