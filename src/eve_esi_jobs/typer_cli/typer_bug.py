from typing import Dict

import click
import typer
from rich import inspect

app = typer.Typer()
app2 = typer.Typer()
app3 = typer.Typer()
app.add_typer(app2, name="schlock")

RULES = {
    "1": "Pillage, then burn.",
    "2": "A Sergeant in motion outranks a Lieutenant who doesn't know what's going on.",
    "3": "An ordnance technician at a dead run outranks everybody.",
    "4": "Close air support covereth a multitude of sins.",
}


@app.callback()
def load_ctx(ctx: typer.Context):
    ctx.obj = {}
    ctx.obj["rules"] = RULES


@app.command()
def hello(ctx: typer.Context, name: str):
    typer.echo(f"Hi {name}")


def autocomplete_rules(ctx: typer.Context):
    # typer.echo(inspect(ctx))
    # typer.echo(repr(ctx.obj))
    rules: Dict = ctx.obj["rules"]
    comps = list(rules.keys())
    return comps


def callback_check(ctx: typer.Context, value: str):
    rules: Dict = ctx.obj["rules"]
    comps = list(rules)
    if value not in comps:
        raise typer.BadParameter(f"Only 1-4 are allowed. tried: {value}")
    return value


@app2.command()
def says(
    ctx: typer.Context,
    index: str = typer.Argument(
        ...,
        help="Choose 1-4.",
        autocompletion=autocomplete_rules,
        callback=callback_check,
    ),
):
    """Choose a saying."""
    typer.echo(ctx.obj["rules"][index])


if __name__ == "__main__":
    app()
