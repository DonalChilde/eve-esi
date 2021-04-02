import json
from pathlib import Path
from typing import Optional

import typer

from eve_esi_jobs.esi_provider import EsiProvider, Op_IdLookup
from eve_esi_jobs.typer_cli.cli_helpers import check_for_op_id, completion_op_id

app = typer.Typer()


@app.command()
def from_op_id(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ..., autocompletion=completion_op_id, callback=check_for_op_id
    ),
    param_string: Optional[str] = typer.Option(None),
    file_path: Optional[Path] = typer.Option(None),
    explain: bool = typer.Option(False, "--explain", "-e"),
    create: bool = typer.Option(False, "--create", "-c"),
):
    """Create a job from op_id and json string

    options - create, explain maybe if not create then explain?
    """
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    if explain and create:
        create = False
    if explain:
        explain_out(op_id, esi_provider)


def explain_out(op_id, esi_provider: EsiProvider):
    op_id_info: Optional[Op_IdLookup] = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        typer.BadParameter(f"{op_id} is not Valid.")
    possible_parameters = op_id_info.parameters
    successful_response = op_id_info.response
    typer.echo(f"op_id: {op_id}")
    typer.echo(f"possible parameters: {json.dumps(possible_parameters,indent=1)}")
    typer.echo(f"returns: {json.dumps(successful_response,indent=1)}")
