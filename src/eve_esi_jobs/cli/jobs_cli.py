import json
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import click

from eve_esi_jobs.eve_esi_jobs import do_jobs
from eve_esi_jobs.model_helpers import pre_process_work_order
from eve_esi_jobs.models import EsiJob, EsiWorkOrder, deserialize_json_work_order
from eve_esi_jobs.pfmsoft.util.file.read_write import load_json


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
    path_in, path_out = validate_in_out_paths(path_in, path_out)
    esi_work_order_json = load_esi_work_order_json(path_in)
    esi_work_order = deserialize_json_work_order(esi_work_order_json)
    # TODO move the ewo initialization to helper, include overrides
    # overrides = {"ewo_name": "override_name"}
    overrides = {}
    esi_work_order.add_param_overrides(overrides)
    pre_process_work_order(esi_work_order)
    esi_provider = ctx.obj["esi_provider"]
    do_jobs(esi_work_order.jobs, esi_provider)


@click.command()
@click.pass_context
def job_skeleton(ctx):
    """output job skeleton files
    -option for more detail, maybe to text file instead of json
    -or just rtfm
    """
    pass


jobs.add_command(run)
jobs.add_command(job_skeleton)


def validate_in_out_paths(path_in, path_out) -> Tuple[Path, Optional[Path]]:
    path_in = Path(path_in)
    if not path_in.exists():
        raise click.UsageError(f"Input path {path_in.resolve()} does not exist.")
    if path_out is not None:
        path_out = Path(path_out)
        if path_out.is_file():
            raise click.UsageError(
                f"Output path {path_out.resolve()} is not a directory."
            )
    return path_in, path_out


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
