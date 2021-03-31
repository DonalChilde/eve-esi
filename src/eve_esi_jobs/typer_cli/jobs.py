"""Running work orders"""
import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, Optional

import typer

from eve_esi_jobs import sample_work_orders
from eve_esi_jobs.eve_esi_jobs import deserialize_json_work_order, do_work_order
from eve_esi_jobs.typer_cli.cli_helpers import load_json, save_json

app = typer.Typer(help="""Work with Esi Jobs and Work Orders.\n\nmore info.""")
logger = logging.getLogger(__name__)


@app.command()
def run(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to Esi Work Order json"),
    path_out: Optional[str] = typer.Option(
        None, help="Path to be prepended to the Esi Work Order path."
    ),
    dry_run: bool = typer.Option(
        False,
        help="""
Dry-run will perform all operations up to but not including making the
actual http requests. This will detect some missed settings and parameters, but does
not find mistakes that can only be checked on the server, eg. a non-existant type_id.
""",
    ),
):
    """Load work orders and run them.

    Dry-run will perform all operations up to but not including making the actual
    http requests. This will detect some missed settings and parameters, but does
    not find mistakes that can only be checked on the server, eg. a non-existant type_id.
    """
    # TODO make validators
    if dry_run:
        typer.BadParameter("not implemented yet.")
    template_overrides = {}
    path_in = validate_input_path(path_in)
    esi_work_order_json = load_esi_work_order_json(Path(path_in))
    esi_work_order = deserialize_json_work_order(esi_work_order_json)
    if path_out is not None:
        path_out = validate_output_path(path_out)
        output_path_string = str(path_out / Path(esi_work_order.parent_path_template))
        template_overrides["ewo_parent_path_template"] = output_path_string
    esi_work_order.add_template_overrides(template_overrides)
    esi_provider = ctx.obj["esi_provider"]
    do_work_order(esi_work_order, esi_provider)
    typer.echo(f"Completed {len(esi_work_order.jobs)} jobs!")
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")
    # logger.info(
    #     "%s Actions sequentially completed -  took %s seconds, %s actions per second.",
    #     len(actions),
    #     f"{seconds:9f}",
    #     f"{len(actions)/seconds:1f}",
    # )


@app.command()
def samples(
    ctx: typer.Context,
    path_out: str = typer.Argument(..., help="Path to output directory."),
):
    """"""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("samples")
    sample_list = [
        sample_work_orders.response_to_job,
        sample_work_orders.result_to_job,
        sample_work_orders.result_to_file_and_response_to_json,
        sample_work_orders.result_and_response_to_job,
        sample_work_orders.result_to_file,
    ]
    typer.echo(f"Sample Esi Work Orders will be saved to {output_path.resolve()}")
    for sample in sample_list:
        ewo = sample()
        file_path = output_path / Path(ewo.name).with_suffix(".json")
        save_json(ewo.dict(), file_path, parents=True)
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")
    # logger.info(
    #     "%s Actions sequentially completed -  took %s seconds, %s actions per second.",
    #     len(actions),
    #     f"{seconds:9f}",
    #     f"{len(actions)/seconds:1f}",
    # )


def validate_input_path(path_in: str) -> str:
    """
    Ensure the input path exists, raise an error and exit the script if it does not.

    Args:
        path_in: The path as a string

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path.
    """
    input_path: Path = Path(path_in)
    if not input_path.exists():
        raise typer.BadParameter(f"Input path {input_path.resolve()} does not exist.")
    return str(input_path)


def validate_output_path(path_out: str) -> str:
    """
    Checks to see if the path is a file.

    Does not check to see if it is a directory, or if it exists.

    Args:
        path_out: the path as a string.

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path
    """
    output_path: Path = Path(path_out)
    if output_path.is_file():
        raise typer.BadParameter(
            f"Output path {output_path.resolve()} is not a directory."
        )
    return str(output_path)


def load_esi_work_order_json(file_path: Path) -> Dict:
    """
    Load a json file. Exit script on error.

    Args:
        file_path: Path to be loaded.

    Raises:
        typer.BadParameter: [description]
        typer.BadParameter: [description]

    Returns:
        The json file.
    """
    try:
        json_data = load_json(file_path)
    except json.decoder.JSONDecodeError as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()} "
            "are you sure it is a json file?"
        )
    except Exception as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()}\n"
            f"The error reported was {ex.__class__} with msg {ex}"
        )
    return json_data
