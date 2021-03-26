from typing import Dict, List

import click

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import AiohttpAction


@click.group()
def history():
    pass


@click.command()
@click.option("--regions", "-r", type=click.STRING)
@click.option("--type_ids", "-t", type=click.STRING)
@click.option("--json", "-j", type=click.File())
@click.option("--csv", "-c", type=click.File())
@click.option(
    "--destination",
    "-d",
    type=click.Choice(["app-dir", "stdout"], case_sensitive=False),
    default="app-dir",
    show_default=True,
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["json", "csv"], case_sensitive=False),
    default="json",
    show_default=True,
)
@click.pass_context
def get(ctx, regions, type_ids, json, csv):

    click.echo("getting market history")


history.add_command(get)


def history_actions(
    region_ids: List[int], type_ids: List[int], esi_provider: EsiProvider
):
    actions: List[AiohttpAction] = []
    for region_id in region_ids:
        for type_id in type_ids:
            path_params = {"region_id": region_id}
            query_params = {"type_id": type_id}
            action = esi_provider.build_action(
                "get_market_history", path_params, query_params
            )
            actions.append(action)
    return actions
