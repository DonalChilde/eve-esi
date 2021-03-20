import click


@click.group()
def history():
    pass


@click.command()
def get():
    click.echo("getting market history")


history.add_command(get)
