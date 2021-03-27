"""entrypoint for eve-esi"""

import click

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.app_data import load_schema
from eve_esi_jobs.cli import history_cli, jobs_cli, schema_cli
from eve_esi_jobs.esi_provider import EsiProvider

# TODO Load schema from file, pass esiprovider through context to registered commands.
# TODO error message if not found
# TODO option to load from specific path.
# TODO option to load config .env from specific path
# TODO generate skeleton config .env


@click.group()
@click.pass_context
def esi_main(ctx):
    ctx.obj = {}
    try:
        schema = load_schema("latest")
        esi_provider = EsiProvider(schema)
        ctx.obj["esi_provider"] = esi_provider
    except Exception as ex:
        click.echo("Esi schema was not found in App Data folder.")


esi_main.add_command(schema_cli.schema)
esi_main.add_command(history_cli.history)
esi_main.add_command(jobs_cli.jobs)
