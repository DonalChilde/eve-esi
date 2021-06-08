"""Working with ESI schema"""

import dataclasses
import json
import logging
import urllib.request
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import typer
import yaml

from eve_esi_jobs.eve_esi_jobs import EveEsiJobs
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
    runner: EveEsiJobs = ctx.obj["runner"]
    try:
        op_info = runner.operation_manifest.op_info(op_id)
    except ValueError:
        raise typer.BadParameter(f"Invalid op_id: {op_id}")
    typer.echo(yaml.dump(dataclasses.asdict(op_info), sort_keys=False))
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
    runner: EveEsiJobs = ctx.obj["runner"]
    op_id_keys = runner.operation_manifest.available_op_ids()
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
    # FIXME move to helpers
    # FIXME check for 200
    # https://stackoverflow.com/a/22530527/105844
    # URL = "https://esi.evetech.net/latest/swagger.json"
    # NOTE response changed as of 3.9 handle deprecated?
    # https://docs.python.org/3/library/urllib.request.html#urllib.response.addinfourl
    with urllib.request.urlopen(url) as response:
        if response.status == 200:
            data = json.loads(
                response.read().decode(response.info().get_param("charset") or "utf-8")
            )
            print(f"Downloaded schema from {url}")
            return data
    return None
