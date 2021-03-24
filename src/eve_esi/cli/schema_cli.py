# """Cli download and manipulation of schema
# TODO option to parse schema for versioned routes?
# TODO option to save multiple copies of schema, allow for choice
#     - this would require a certain ammount of dynamic validation.
# """
# import asyncio
# import json
# from typing import Any, Dict

# import click

# from eve_esi_jobs.actions import get_schema
# from eve_esi_jobs.app_config import logger
# from eve_esi_jobs.app_data import save_json_to_app_data
# from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
#     AiohttpQueueWorker,
#     do_aiohttp_action_queue,
# )
# from eve_esi_jobs.pfmsoft.util.file.read_write import load_json


# @click.group()
# def schema():
#     pass


# @click.command()
# @click.option(
#     "--source",
#     "-s",
#     type=click.Choice(["download", "file"], case_sensitive=False),
#     default="download",
#     show_default=True,
# )
# @click.option(
#     "--destination",
#     "-d",
#     type=click.Choice(["app-dir", "stdout"], case_sensitive=False),
#     default="app-dir",
#     show_default=True,
# )
# @click.option("--source-url")
# def get(source, destination, source_url):
#     # TODO strat to pass back reasonable error messages.
#     # Maybe a try catch in download schema?

#     if source == "download":
#         schema_ = download_schema()
#     if source == "file":
#         try:
#             schema_ = load_json(source_url)
#         except Exception as ex:
#             raise click.ClickException(
#                 f"Unable to load file from {source_url} with error message: {ex}"
#             )
#     if schema_ is None:
#         raise click.ClickException("Error loading schema.")
#     if destination == "app-dir":
#         version = schema_["info"]["version"]
#         params = {"version": version}
#         file_path = save_json_to_app_data(schema_, "schema", params)
#         click.echo(f"Schema saved to {file_path}")
#     if destination == "stdout":
#         # rich console overflow not compat with pipe to file.
#         print(json.dumps(schema_, indent=2))


# @click.command()
# @click.pass_context
# def test(ctx):
#     esi_provider = ctx.obj["esi_provider"]

#     print(json.dumps(esi_provider.op_id_lookup, indent=2))


# schema.add_command(get)
# schema.add_command(test)


# def download_schema() -> Dict[Any, Any]:
#     action = get_schema()
#     worker = AiohttpQueueWorker()
#     asyncio.run(do_aiohttp_action_queue([action], [worker]))
#     return action.result
