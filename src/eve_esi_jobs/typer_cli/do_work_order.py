"""Running work orders"""

import logging
from pathlib import Path
from typing import List, Optional

import typer

from eve_esi_jobs.eve_esi_jobs import do_work_order
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (  # load_esi_work_order_json,
    FormatChoices,
    report_finished_task,
    validate_input_path,
    validate_output_path,
)
from eve_esi_jobs.typer_cli.observer import EsiObserver

app = typer.Typer(help="""Do jobs and workorders.\n\nmore info.""")
logger = logging.getLogger(__name__)


@app.command()
def job(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to the job file."),
    path_out: Optional[str] = typer.Argument(
        None, help="Path to be prepended to the job output path."
    ),
    dry_run: bool = typer.Option(
        False,
        "-d",
        "--dry-run",
        help="""
Not implemented yet.
Dry-run will perform all operations up to but not including making the
actual http requests. This will detect some missed settings and parameters, but does
not find mistakes that can only be checked on the server, eg. a non-existant type_id.
""",
    ),
):
    """Load a job from a file and do it."""
    if dry_run:
        typer.BadParameter("not implemented yet.")
    path_in = validate_input_path(path_in)
    file_path = Path(path_in)
    try:
        esi_job = EsiJob.deserialize_file(file_path)
    except Exception as ex:
        logger.exception(
            "Error deserializing job from file: %s. Error: %s, msg: %s",
            file_path,
            ex.__class__.__name__,
            ex,
        )
        raise typer.BadParameter(f"Error decoding job at {file_path}, msg:{ex}")
    if path_out is not None:
        # print(path_out)
        # NOTE: path is not checked with results of template values.
        path_out = validate_output_path(path_out)
        # output_path_string = str(path_out / Path(esi_work_order.parent_path_template))
        # esi_job.update_attributes({"ewo_parent_path_template": str(path_out)})
    esi_provider = ctx.obj["esi_provider"]
    ewo_ = EsiWorkOrder()
    ewo_.output_path = str(path_out)
    ewo_.jobs.append(esi_job)
    observer = EsiObserver()
    do_work_order(ewo_, esi_provider, observers=[observer])
    print(repr(esi_job))
    report_on_jobs(ewo_.jobs)
    report_finished_task(ctx)


@app.command()
def workorder(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to the workorder file."),
    path_out: Optional[str] = typer.Argument(
        None, help="Path to be prepended to the workorder output path."
    ),
    dry_run: bool = typer.Option(
        False,
        "-d",
        "--dry-run",
        help="""
Not implemented yet.
Dry-run will perform all operations up to but not including making the
actual http requests. This will detect some missed settings and parameters, but does
not find mistakes that can only be checked on the server, eg. a non-existant type_id.
""",
    ),
):
    """Load a workorder and do it."""

    if dry_run:
        typer.BadParameter("not implemented yet.")
    path_in = validate_input_path(path_in)
    file_path = Path(path_in)
    try:
        esi_work_order = EsiWorkOrder.deserialize_file(file_path)
    except Exception as ex:
        logger.exception(
            "Error deserializing workorder from file: %s. Error: %s, msg: %s",
            file_path,
            ex.__class__.__name__,
            ex,
        )
        raise typer.BadParameter(f"Error decoding workorder at {file_path}, msg: {ex}")
    if path_out is not None:
        # NOTE: path is not checked with results of template values.
        path_out = validate_output_path(path_out)
        output_path_string = str(path_out / Path(esi_work_order.output_path))
        esi_work_order.update_attributes({"ewo_output_path": output_path_string})
    esi_provider = ctx.obj["esi_provider"]
    observer = EsiObserver()
    do_work_order(esi_work_order, esi_provider, observers=[observer])
    report_on_jobs(esi_work_order.jobs)
    report_finished_task(ctx)


def report_on_jobs(esi_jobs: List[EsiJob]):
    successes = 0
    failures = 0
    no_info = len(esi_jobs)
    # jobs with retries?
    for job_ in esi_jobs:
        if job_.result is not None and job_.result.response is not None:
            status = job_.result.response.get("status", None)
            if status == 200:
                successes += 1
                no_info -= 1
            elif status != 200 and status is not None:
                failures += 1
                no_info -= 1
    typer.echo(
        f"Network response -> Successes: {successes}, Failures: {failures}, "
        f"Not Reporting: {no_info}"
    )
    typer.echo("see logs for details.")
    typer.echo(f"Completed {len(esi_jobs)} jobs!")
