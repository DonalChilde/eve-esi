"""entrypoint for eve-esi"""
import logging

import click

from eve_esi.cli import history_cli, schema_cli

logger = logging.getLogger(__name__)


@click.group()
def esi_main():
    pass


@click.group()
def esi():
    pass


esi_main.add_command(schema_cli.schema)
esi_main.add_command(history_cli.history)
