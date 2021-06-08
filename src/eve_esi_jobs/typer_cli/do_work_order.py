"""Running work orders"""

import logging
from pathlib import Path
from typing import List, Optional

import typer

from eve_esi_jobs.eve_esi_jobs import EveEsiJobs
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (
    report_finished_task,
    validate_input_path,
    validate_output_path,
)

app = typer.Typer(help="""Do jobs and workorders.""")
logger = logging.getLogger(__name__)


@app.command()
def job(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to the job file."),
    path_out: str = typer.Argument(
        "./tmp", help="Path to be prepended to the job output path."
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
    runner: EveEsiJobs = ctx.obj["runner"]
    try:
        esi_job = runner.deserialize_job(file_path)
    except Exception as ex:
        logger.exception(
            "Error deserializing job from file: %s. Error: %s, msg: %s",
            file_path,
            ex.__class__.__name__,
            ex,
        )
        raise typer.BadParameter(f"Error decoding job at {file_path}, msg:{ex}")

    # NOTE: path is not checked with results of template values.
    path_out = validate_output_path(path_out)

    ewo = EsiWorkOrder(output_path=str(path_out))
    ewo.jobs.append(esi_job)
    # observer = EsiObserver()
    try:
        runner.do_workorder(ewo)
    except Exception as ex:
        raise typer.BadParameter(f"Error doing the job. {ex.__class__.__name__}: {ex}")
    report_on_jobs(ewo.jobs)
    report_finished_task(ctx)


@app.command()
def workorder(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to the workorder file."),
    path_out: str = typer.Argument(
        "./tmp", help="Path to be prepended to the workorder output path."
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
    runner: EveEsiJobs = ctx.obj["runner"]
    try:
        ewo = runner.deserialize_workorder(file_path)
    except Exception as ex:
        logger.exception(
            "Error deserializing workorder from file: %s. Error: %s, msg: %s",
            file_path,
            ex.__class__.__name__,
            ex,
        )
        raise typer.BadParameter(f"Error decoding workorder at {file_path}, msg: {ex}")

    # NOTE: path is not checked with results of template values.
    path_out = validate_output_path(path_out)
    output_path_string = str(path_out / Path(ewo.output_path))

    # observer = EsiObserver()
    try:
        runner.do_workorder(
            workorder=ewo, override_values={"ewo_output_path": output_path_string}
        )
    except Exception as ex:
        raise typer.BadParameter(f"Error doing the job. {ex.__class__.__name__}: {ex}")
    report_on_jobs(ewo.jobs)
    report_finished_task(ctx)


def report_on_jobs(esi_jobs: List[EsiJob]):
    successes = 0
    failures = 0
    no_info = len(esi_jobs)
    # jobs with retries?
    # FIXME local vs remote vs 304?
    for esi_job in esi_jobs:
        if esi_job.result is not None and esi_job.result.response is not None:
            status = esi_job.result.response.status
            if status == 200:
                successes += 1
                no_info -= 1
            elif status != 200 and status is not None:
                failures += 1
                no_info -= 1
    typer.echo(
        f"Fix this output!\n"
        f"Network response -> Successes: {successes}, Failures: {failures}, "
        f"Not Reporting: {no_info}"
    )
    typer.echo("see logs for details.")
    typer.echo(f"Completed {len(esi_jobs)} jobs!")
