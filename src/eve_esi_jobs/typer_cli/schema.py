"""Working with ESI schema"""

import dataclasses
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import typer
import yaml
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import do_action_runner

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.typer_cli.app_config import EveEsiJobConfig
from eve_esi_jobs.typer_cli.app_data import save_json_to_app_data
from eve_esi_jobs.typer_cli.cli_helpers import (
    check_for_op_id,
    completion_op_id,
    report_finished_task,
)

logger = logging.getLogger(__name__)
app = typer.Typer(help="Download, save, and inspect Esi schemas.")


@app.command()
def browse(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        "get_markets_prices",
        autocompletion=completion_op_id,
        callback=check_for_op_id,
        help="A valid op-id. e.g. get_markets_prices",
    ),
):
    """Browse schema by op_id."""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        typer.BadParameter(f"Invalid op_id: {op_id}")
    typer.echo(yaml.dump(dataclasses.asdict(op_id_info), sort_keys=False))
    report_finished_task(ctx)


class OpidOutput(Enum):
    LIST = "raw-list"
    JSON = "json"


@app.command()
def list_op_ids(
    ctx: typer.Context,
    output: OpidOutput = typer.Option(
        "raw-list",
        "-o",
        "--output",
        show_choices=True,
        help="Output format.",
    ),
):
    """List available op_ids."""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_keys = list(esi_provider.op_id_lookup)
    op_id_keys.sort()
    if output == OpidOutput.JSON:
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
        help="The url to the ESI schema.",
    ),
    std_out: bool = typer.Option(
        False, "-s", "--std-out", help="Print schema to std out"
    ),
    app_data: bool = typer.Option(
        True, help="Save the schema to the app data directory."
    ),
    file_path: Path = typer.Option(
        None, "-f", "--file-path", help="Custom path for saving schema."
    ),
):
    """Download a schema, use --help for more options."""
    config: EveEsiJobConfig = ctx.obj["config"]
    url = config.schema_url
    schema: Optional[Dict] = download_json(url)
    if schema is None:
        raise typer.BadParameter(f"Unable to download schema from {url}")
    if app_data:
        # pylint: disable=unsubscriptable-object
        version = schema["info"]["version"]  # type: ignore
        params = {"version": version}
        save_path = save_json_to_app_data(schema, config.app_dir, "schema", params)
        typer.echo(f"Schema saved to {save_path}")
    if std_out:
        typer.echo(json.dumps(schema, indent=2))
        typer.Exit()
    if file_path is not None:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(schema))
        except Exception as ex:
            raise typer.BadParameter(
                f"Error saving schema to {file_path}. Error: {ex.__class__.__name__}, msg: {ex}"
            )
        typer.echo(f"Schema saved to {file_path.resolve()}")
    report_finished_task(ctx)


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
    typer.echo(
        f"Url: {url} failed with code: {action.response.status} {action.response.reason}"
    )
    return None
