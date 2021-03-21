"""Cli download and manipulation of schema
TODO option to parse schema for versioned routes?
TODO option to save multiple copies of schema, allow for choice
    - this would require a certain ammount of dynamic validation.
"""
import asyncio
from pathlib import Path
from typing import Any, Dict

import click

from eve_esi.actions import get_schema
from eve_esi.app_config import APP_NAME
from eve_esi.app_data import load_json_from_app_data, save_json_to_app_data
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpQueueWorker,
    do_aiohttp_action_queue,
)


@click.group()
def schema():
    pass


@click.command()
# @click.option()
def get():
    # TODO options:
    # download
    #    to save to app data,
    #    save to specific path
    #    or print to stdout
    # load from app data
    #    save to specific path
    #    or print to stdout
    click.echo("getting json schema")
    schema_ = download_schema()
    if schema_ is not None:
        file_path = save_json_to_app_data(schema_, "schema")
        click.echo(f"Schema saved to {file_path}")
    else:
        # TODO strat to pass back reasonable error messages.
        # Maybe a try catch in download schema?
        click.echo("Error downloading schema.")


def download_schema() -> Dict[Any, Any]:
    action = get_schema()
    worker = AiohttpQueueWorker()
    asyncio.run(do_aiohttp_action_queue([action], [worker]))
    return action.result
