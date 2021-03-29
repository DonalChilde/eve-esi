"""Run work orders found in json files."""
import json
from pathlib import Path
from typing import Dict

import click

from eve_esi_jobs import sample_work_orders
from eve_esi_jobs.eve_esi_jobs import deserialize_json_work_order, do_work_order
from eve_esi_jobs.helpers import load_json, save_json


@click.group()
@click.pass_context
def jobs(ctx):
    pass


@click.command()
@click.argument("path_in")
@click.argument("path_out", required=False)
@click.option(
    "--dry-run",
    "-d",
    type=click.BOOL,
    help="Not Implemented Yet. Perform a dry run on work order.",
)
@click.pass_context
def run(ctx, path_in, path_out, dry_run):
    """Load work orders and run them.

    Dry-run will perform all operations up to but not including making the actual
    http requests. This will detect some missed settings and parameters, but does
    not find mistakes that can only be checked on the server, eg. a non-existant type_id.
    """
    if dry_run:
        click.ClickException("not implemented yet.")
    overrides = {}
    path_in = validate_input_path(path_in)
    esi_work_order_json = load_esi_work_order_json(path_in)
    esi_work_order = deserialize_json_work_order(esi_work_order_json)
    if path_out is not None:
        path_out: Path = validate_output_path(path_out)
        output_path_string = str(path_out / Path(esi_work_order.parent_path_template))
        overrides["ewo_parent_path_template"] = output_path_string
    esi_work_order.add_param_overrides(overrides)
    esi_provider = ctx.obj["esi_provider"]
    do_work_order(esi_work_order, esi_provider)


@click.command()
@click.argument("path_out", required=False)
@click.pass_context
def work_order_samples(ctx, path_out):
    """Output sample work orders."""

    if path_out is not None:
        output_path = validate_output_path(path_out)
        output_path = output_path / Path("samples")
    else:
        output_path = Path("samples")
    sample_list = [
        sample_work_orders.response_to_job,
        sample_work_orders.result_to_job,
        sample_work_orders.result_to_file_and_response_to_json,
        sample_work_orders.result_and_response_to_job,
        sample_work_orders.result_to_file,
    ]
    click.echo(f"Sample Esi work orders will be saved to {output_path.resolve()}")
    for sample in sample_list:
        ewo = sample()
        file_path = output_path / Path(ewo.name).with_suffix(".json")
        save_json(ewo.dict(), file_path, parents=True)


jobs.add_command(run)
jobs.add_command(work_order_samples)


def validate_input_path(path_in: str) -> Path:
    """
    Ensure the input path exists, raise an error and exit the script if it does not.

    Args:
        path_in: The path as a string

    Raises:
        click.UsageError:

    Returns:
        The path string as a Path.
    """
    input_path: Path = Path(path_in)
    if not input_path.exists():
        raise click.UsageError(f"Input path {input_path.resolve()} does not exist.")
    return input_path


def validate_output_path(path_out: str) -> Path:
    """
    Checks to see if the path is a file.

    Does not check to see if it is a directory, or if it exists.

    Args:
        path_out: the path as a string.

    Raises:
        click.UsageError:

    Returns:
        The path string as a Path
    """
    output_path: Path = Path(path_out)
    if output_path.is_file():
        raise click.UsageError(
            f"Output path {output_path.resolve()} is not a directory."
        )
    return output_path


def load_esi_work_order_json(file_path: Path) -> Dict:
    """
    Load a json file. Exit script on error.

    Args:
        file_path: Path to be loaded.

    Raises:
        click.UsageError: [description]
        click.UsageError: [description]

    Returns:
        The json file.
    """
    try:
        json_data = load_json(file_path)
    except json.decoder.JSONDecodeError as ex:
        raise click.UsageError(
            f"Error loading json file at {file_path.resolve()} "
            "are you sure it is a json file?"
        )
    except Exception as ex:
        raise click.UsageError(
            f"Error loading json file at {file_path.resolve()}\n"
            f"The error reported was {ex.__class__} with msg {ex}"
        )
    return json_data
