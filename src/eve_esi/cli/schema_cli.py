"""Cli download and manipulation of schema"""
import asyncio
from pathlib import Path
from typing import Any, Dict

import click

from eve_esi.actions import get_schema
from eve_esi.app_config import APP_NAME
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpQueueWorker,
    do_aiohttp_action_queue,
)
from eve_esi.pfmsoft.util.file.read_write import load_json, save_json


@click.group()
def schema():
    pass


@click.command()
# @click.option()
def get():
    click.echo("getting json schema")
    schema_ = download_schema()
    if schema_ is not None:
        save_schema(schema_)
    else:
        # TODO strat to pass back reasonable error messages.
        # Maybe a try catch in download schema?
        click.echo("Error downloading schema.")


def save_schema(schema):
    file_path = save_json_to_config(schema, APP_NAME, "schema", "esi_schema.json")
    click.echo(f"Schema saved to {file_path}")


def load_schema() -> Dict:
    schema = load_json_from_config(APP_NAME, "schema", "esi_schema.json")
    return schema


def save_routes(schema):
    routes = make_routes(schema)
    file_path = save_json_to_config(routes, APP_NAME, "schema", "esi_routes.json")
    click.echo(f"Routes saved to {file_path}")


def load_routes() -> Dict:
    routes = load_json_from_config(APP_NAME, "schema", "esi_routes.json")
    return routes


def load_json_from_config(app_name: str, data_path, file_name) -> Dict:
    config_path: Path = Path(click.get_app_dir(app_name, force_posix=True))
    sub_path: Path = Path(data_path)
    file_path: Path = config_path / sub_path / Path(file_name)
    data = load_json(file_path)
    return data


def save_json_to_config(data, app_name: str, data_path, file_name) -> Path:
    config_path: Path = Path(click.get_app_dir(app_name, force_posix=True))
    sub_path: Path = Path(data_path)
    file_path: Path = config_path / sub_path / Path(file_name)
    save_json(data, file_path, parents=True)
    return file_path


def make_routes(schema) -> Dict:
    routes = build_operation_id_lookup(schema)
    return routes


def download_schema() -> Dict[Any, Any]:
    action = get_schema()
    worker = AiohttpQueueWorker()
    asyncio.run(do_aiohttp_action_queue([action], [worker]))
    return action.result


def build_operation_id_lookup(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build a lookup table from the Esi schema.

    Extracts all the available routes, and converts any bracketed
    parameters to python string template format. e.g.
    /foo/{region}/bar
    to
    /foo/${region}/bar

    Parameters
    ----------
    schema : Dict[str, Any]
        The Esi swagger schema

    Returns
    -------
    Dict[str, Dict[str, Any]]
        The lookup table.
    """
    lookup = {}
    lookup["host"] = schema["host"]
    lookup["info"] = schema["info"]
    lookup["basePath"] = schema["basePath"]
    lookup["parameters"] = schema["parameters"]
    lookup["routes"] = {}
    for route, route_schema in schema["paths"].items():
        for method, method_schema in route_schema.items():
            lookup_key = method_schema["operationId"]
            lookup["routes"][lookup_key] = {
                "method": method,
                "route": route,
                "template_route": route.replace("{", "${"),
                "parameters": method_schema["parameters"],
                "responses": method_schema["responses"],
            }
    return lookup
