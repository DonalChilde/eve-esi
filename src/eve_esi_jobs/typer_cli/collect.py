import json
import logging
from pathlib import Path
from string import Template
from typing import Optional

import typer

from eve_esi_jobs.eve_esi_jobs import (
    deserialize_job_from_dict,
    deserialize_work_order_from_string,
    serialize_work_order,
)
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import load_json, save_string

app = typer.Typer()
logger = logging.getLogger(__name__)

DEFAULT_WORKORDER = EsiWorkOrder(
    parent_path_template="workorders/${ewo_iso_date_time}/workorder-${ewo_uid}"
)


@app.command()
def jobs(
    ctx: typer.Context,
    path_in: Path = typer.Argument(...),
    path_out: Path = typer.Argument("."),
    file_name: Path = typer.Option(
        "workorders/${ewo_iso_date_time}/workorder-${ewo_uid}.json",
        "-f",
        "--file-name",
        help="file name for the work order. Can include directories.",
    ),
    ewo_string: Optional[str] = typer.Option(None, "-w", "--work-order"),
):
    # TODO change ewo_string to a json file path
    if not path_in.exists():
        raise typer.BadParameter(f"{path_in} does not exist.")
    loaded_jobs = []
    if path_in.is_file():
        loaded_job = load_job(path_in)
        if loaded_job is not None:
            loaded_jobs.append(loaded_job)
    if path_in.is_dir():
        maybe_jobs = path_in.glob("*.json")
        for maybe_job in maybe_jobs:
            loaded_job = load_job(maybe_job)
            if loaded_job is not None:
                loaded_jobs.append(loaded_job)
    if not loaded_jobs:
        raise typer.BadParameter(f"No jobs found at {path_in}")
    if ewo_string is None:
        ewo = DEFAULT_WORKORDER.copy()
    else:
        try:
            ewo = deserialize_work_order_from_string(ewo_string)
        except Exception as ex:
            raise typer.BadParameter(
                f"Error decoding work order string. {ex.__class__.__name__}, {ex}"
            )
    ewo.jobs.extend(loaded_jobs)
    output_path = path_out / file_name
    out_template = Template(str(output_path))
    out_string = out_template.substitute(ewo.attributes())
    out_path_from_template = Path(out_string)
    # if out_path_from_template.is_file():
    #     raise typer.BadParameter(
    #         f"{out_path_from_template} is a file, should be a directory."
    #     )
    try:
        save_string(serialize_work_order(ewo), out_path_from_template, parents=True)
    except Exception as ex:
        raise typer.BadParameter(
            f"Error saving work order to {path_out}. {ex.__class__.__name__}, {ex}"
        )


def load_job(file_path: Path) -> Optional[EsiJob]:
    try:
        data = load_json(file_path)
    except Exception as ex:  # pylint: disable=broad-except
        typer.echo(f"Error loading job from {file_path}. {ex.__class__.__name__}, {ex}")
        return None
    try:
        job = deserialize_job_from_dict(data)
        return job
    except Exception as ex:
        raise typer.BadParameter(
            f"{file_path} is not a valid EsiJob. {ex.__class__.__name__}, {ex}"
        )
