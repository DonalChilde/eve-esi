"""Console script for eve_esi."""

import sys

import click


@click.command()
def main(args=None):
    """Console script for eve_esi."""
    click.echo("Replace this message by putting your code into " "eve_esi.cli.main")
    click.echo(args)
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
