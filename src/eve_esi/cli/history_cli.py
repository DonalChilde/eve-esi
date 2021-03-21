import click


@click.group()
def history():
    pass


@click.command()
@click.option("--regions", "-r", type=click.STRING)
@click.option("--type_ids", "-t", type=click.STRING)
@click.option("--json", "-j", type=click.File)
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
def get(regions, type_ids, json):

    click.echo("getting market history")


history.add_command(get)
