import json
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import click

from eve_esi_jobs import sample_work_orders
from eve_esi_jobs.eve_esi_jobs import do_work_order
from eve_esi_jobs.model_helpers import pre_process_work_order
from eve_esi_jobs.models import EsiJob, EsiWorkOrder, deserialize_json_work_order
from eve_esi_jobs.pfmsoft.util.file.read_write import load_json, save_json


@click.group()
@click.pass_context
def jobs(ctx):
    pass


@click.command()
@click.argument("path_in")
@click.argument("path_out", required=False)
@click.option("--validate", "-v", type=click.BOOL)
@click.pass_context
def run(ctx, path_in, path_out, validate):
    """load json files and run them
    - validate option
    - no action option
    - load defaults from app data
    """
    overrides = {}
    path_in = validate_input_path(path_in)
    esi_work_order_json = load_esi_work_order_json(path_in)
    esi_work_order = deserialize_json_work_order(esi_work_order_json)
    if path_out is not None:
        path_out = validate_output_path(path_out)
        esi_work_order.parent_path_template = (
            path_out / esi_work_order.parent_path_template
        )
    esi_work_order.add_param_overrides(overrides)
    esi_provider = ctx.obj["esi_provider"]
    do_work_order(esi_work_order, esi_provider)


@click.command()
@click.argument("path_out", required=False)
@click.pass_context
def work_order_samples(ctx, path_out):
    """output job skeleton files
    -option for more detail, maybe to text file instead of json
    -or just rtfm
    """

    if path_out is not None:
        output_path = validate_output_path(path_out)
        output_path = output_path / Path("samples")
    else:
        output_path = Path("samples")
    ewo = sample_work_orders.response_to_job()
    file_path = output_path / Path(ewo.name).with_suffix(".json")
    save_json(ewo.dict(), file_path, parents=True)


jobs.add_command(run)
jobs.add_command(work_order_samples)


def validate_input_path(path_in: str) -> Path:
    input_path: Path = Path(path_in)
    if not input_path.exists():
        raise click.UsageError(f"Input path {input_path.resolve()} does not exist.")
    return input_path


def validate_output_path(path_out: str) -> Path:
    output_path: Path = Path(path_out)
    if output_path.is_file():
        raise click.UsageError(
            f"Output path {output_path.resolve()} is not a directory."
        )
    return output_path


# def validate_in_out_paths(path_in, path_out) -> Tuple[Path, Optional[Path]]:
#     path_in = Path(path_in)
#     if not path_in.exists():
#         raise click.UsageError(f"Input path {path_in.resolve()} does not exist.")
#     if path_out is not None:
#         path_out = Path(path_out)
#         if path_out.is_file():
#             raise click.UsageError(
#                 f"Output path {path_out.resolve()} is not a directory."
#             )
#     return path_in, path_out


def load_esi_work_order_json(file_path: Path) -> Dict:
    try:
        esi_work_order_json = load_json(file_path)
    except json.decoder.JSONDecodeError as ex:
        raise click.UsageError(
            f"Error loading esi-jobs file at {file_path.resolve()} are you sure it is a json file?"
        )
    except Exception as ex:
        raise click.UsageError(
            f"Error loading esi-jobs file at {file_path.resolve()}\nThe error reported was {ex.__class__} with msg {ex}"
        )
    return esi_work_order_json
