### Describe the bug

I have an expensive object stored in the context obj for use in my sub commands.
I expected to be able to pull that object out of the ctx.obj in my autocompletion function and use it to generate the completion list.
There is a ctx object, but it has no ctx.obj. However, my callbacks that use ctx.obj work as expected.

### To Reproduce

Steps to reproduce the behavior with a minimum self-contained file.

Replace each part with your own scenario:

- Create a file `main.py` with:

```Python
from typing import Dict
import typer

app = typer.Typer()
app2 = typer.Typer()
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
    rules: Dict = ctx.obj["rules"]
    comps = list(rules)
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
```

- Call it with:

```bash
typer main.py run schlock says [tab][tab]
```

- It outputs:

```text
File "/home/chad/projects/eve/eve_esi/.venv/lib/python3.9/site-packages/typer/main.py", line 850, in wrapper
    return callback(**use_params)  # type: ignore
  File "src/eve_esi_jobs/typer_cli/typer_bug.py", line 28, in autocomplete_rules
    rules: Dict = ctx.obj["rules"]
TypeError: 'NoneType' object is not subscriptable
```

- But I expected it to output:

```text
1 2 3 4
```

### Expected behavior

I expected be be able to access the context in autocompletion function.
If you try a value of 5, you can see that the context is available in the callback function.

### Screenshots

If applicable, add screenshots to help explain your problem.

### Environment

- OS: pop_os 20.10
- Typer Version 0.3.2

```bash
python -c "import typer; print(typer.__version__)"
```

- Python version, get it with:

python 3.9.0

### Additional context

Add any other context about the problem here.
