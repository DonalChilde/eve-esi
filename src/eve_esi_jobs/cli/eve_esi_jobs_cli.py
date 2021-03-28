"""This is the starting point for the eve-esi cli interface.

The command groups are assembled here. An instance of :class:`EsiProvider` is
also created and attatched to the context.obj for later use. If a valid
ESI schema cannot be found, an error will be reported but the script will not halt.
It is assumed the next step would be to download one.

TODO: change the behavior to automatically attempt download if schema not found?
TODO: make this eve-esi
                        schema
                        run
                        samples

"""


import click

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.app_data import load_schema
from eve_esi_jobs.cli import history_cli, jobs_cli, schema_cli
from eve_esi_jobs.esi_provider import EsiProvider

# TODO option to load from specific path.
# TODO option to load config .env from specific path
# TODO generate skeleton config .env


@click.group()
@click.pass_context
def esi_main(ctx: click.Context):
    """
    Welcome to Eve Esi Jobs. Try one of the commands below.
    """

    ctx.obj = {}
    try:
        schema = load_schema("latest")
        esi_provider = EsiProvider(schema)
        ctx.obj["esi_provider"] = esi_provider
    except Exception as ex:
        click.echo("Esi schema was not found in App Data folder.")


esi_main.add_command(schema_cli.schema)
# esi_main.add_command(history_cli.history)
esi_main.add_command(jobs_cli.jobs)
