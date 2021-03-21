"""entrypoint for eve-esi"""
import logging

import click

from eve_esi.cli import history_cli, schema_cli

logger = logging.getLogger(__name__)

# TODO Load schema from file, pass esiprovider through context to registered commands.
# TODO error message if not found
# TODO option to load from specific path.
# TODO option to load config .env from specific path
# TODO generate skeleton config .env


@click.group()
def esi_main():
    pass


esi_main.add_command(schema_cli.schema)
esi_main.add_command(history_cli.history)
