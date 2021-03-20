import asyncio
import logging
from asyncio import Task, create_task, gather
from asyncio.queues import Queue
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Coroutine, Dict, Sequence

import click
from aiohttp import ClientSession

from eve_esi.actions import get_schema
from eve_esi.cli import history_cli
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpQueueWorker,
    do_aiohttp_action_queue,
)
from eve_esi.pfmsoft.util.file.read_write import load_json, save_json

logger = logging.getLogger(__name__)
APP_NAME = "Eve Esi"


@click.group()
def esi_main():
    pass


@click.group()
def esi():
    pass


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
        save_routes(schema_)
    else:
        # TODO strat to pass back reasonable error messages.
        # Maybe a try catch in download schema?
        click.echo("Error downloading schema.")


esi.add_command(schema)
schema.add_command(get)
esi_main.add_command(esi)
esi_main.add_command(history_cli.history)


def save_schema(schema):
    # config_path: Path = Path(click.get_app_dir(APP_NAME, force_posix=True))
    # schema_path: Path = Path("schema")
    # file_name: Path = Path("esi_schema.json")
    # file_path: Path = config_path / schema_path / file_name
    # save_json(schema, file_path, parents=True)
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


def download_schema() -> Dict[Any, Any]:
    action = get_schema()
    worker = AiohttpQueueWorker()
    asyncio.run(do_aiohttp_action_queue([action], [worker]))
    return action.result


# async def do_aiohttp_actions(
#     actions: AiohttpAction,
#     worker_factories: Sequence[AiohttpQueueWorker],
#     session_kwargs=None,
# ):
#     start = perf_counter_ns()
#     if session_kwargs is None:
#         session_kwargs = {}
#     queue: Queue = Queue()
#     async with ClientSession(**session_kwargs) as session:
#         logger.info(
#             "Starting queue with %s workers and %s actions",
#             len(worker_factories),
#             len(actions),
#         )

#         worker_tasks = []
#         for factory in worker_factories:
#             worker_task: Task = create_task(factory.get_worker(queue, session))
#             worker_tasks.append(worker_task)
#         logger.info("Adding %d actions to queue", len(actions))
#         for action in actions:
#             queue.put_nowait(action)
#         await queue.join()
#         for worker_task in worker_tasks:
#             worker_task.cancel()
#         await gather(*worker_tasks, return_exceptions=True)
#         end = perf_counter_ns()
#         # TODO change timing formatter to lib method
#         seconds = (end - start) / 1000000000
#         logger.info(
#             "Queue completed -  took %s seconds, %s actions per second.",
#             f"{seconds:9f}",
#             f"{len(actions)/seconds:1f}",
#         )
