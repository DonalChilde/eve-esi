"""Running work orders"""

import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Callable, List, Optional, Sequence

import typer

from eve_esi_jobs.callback_manifest import DefaultCallbackFactory
from eve_esi_jobs.eve_esi_jobs import (
    deserialize_job_from_string,
    deserialize_work_order_from_string,
    do_jobs,
    do_work_order,
    serialize_job,
    serialize_work_order,
)
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (  # load_esi_work_order_json,
    FormatChoices,
    report_finished_task,
    validate_input_path,
    validate_output_path,
)

app = typer.Typer(help="""Do Jobs and Work Orders.\n\nmore info.""")
logger = logging.getLogger(__name__)


@app.command()
def job(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to Esi Work Order json"),
    path_out: Optional[str] = typer.Argument(
        None, help="Path to be prepended to the Esi Work Order path."
    ),
    format_id: FormatChoices = typer.Option(
        FormatChoices.json,
        "-f",
        "--format-id",
        show_choices=True,
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
    """Load Jobs and run them."""
    if dry_run:
        typer.BadParameter("not implemented yet.")
    path_in = validate_input_path(path_in)
    file_path = Path(path_in)
    job_string = file_path.read_text()
    # esi_job_json = load_esi_job_json(Path(path_in))
    try:
        esi_job = deserialize_job_from_string(job_string, format_id)
    except Exception as ex:
        logger.exception(
            "Error deserializing job from file: %s data: %s",
            file_path,
            job_string,
        )
        raise typer.BadParameter(f"Error decoding job at {file_path}")
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
    do_work_order(ewo_, esi_provider)
    print(repr(esi_job))
    report_on_jobs(ewo_.jobs)
    report_finished_task(ctx)


@app.command()
def ewo(
    ctx: typer.Context,
    path_in: str = typer.Argument(..., help="Path to Esi Work Order json"),
    path_out: Optional[str] = typer.Argument(
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
    """Load Work Orders and run them.

    Dry-run will perform all operations up to but not including making the actual
    http requests. This will detect some missed settings and parameters, but does
    not find mistakes that can only be checked on the server, eg. a non-existant type_id.
    """

    if dry_run:
        typer.BadParameter("not implemented yet.")
    path_in = validate_input_path(path_in)
    file_path = Path(path_in)
    ewo_string = file_path.read_text()
    # esi_work_order_json = load_esi_work_order_json(Path(path_in))
    try:
        esi_work_order = deserialize_work_order_from_string(ewo_string, "json")
    except Exception as ex:
        logger.exception(
            "Error deserializing work order from file: %s data: %s",
            file_path,
            ewo_string,
        )
        raise typer.BadParameter(f"Error decoding work order at {file_path}")
    if path_out is not None:
        # NOTE: path is not checked with results of template values.
        path_out = validate_output_path(path_out)
        output_path_string = str(path_out / Path(esi_work_order.parent_path_template))
        esi_work_order.update_attributes(
            {"ewo_parent_path_template": output_path_string}
        )
    esi_provider = ctx.obj["esi_provider"]
    do_work_order(esi_work_order, esi_provider)
    report_on_jobs(esi_work_order.jobs)
    report_finished_task(ctx)


def report_on_jobs(esi_jobs: List[EsiJob]):
    successes = 0
    failures = 0
    no_info = len(esi_jobs)
    # jobs with retries?
    for job in esi_jobs:
        if job.result is not None and job.result.response is not None:
            status = job.result.response.get("status", None)
            if status == 200:
                successes += 1
                no_info -= 1
            elif status != 200 and status is not None:
                failures += 1
                no_info -= 1
    typer.echo(
        f"Successes: {successes}, Failures: {failures}, Not Reporting: {no_info}"
    )
    typer.echo("see logs for details.")
    typer.echo(f"Completed {len(esi_jobs)} jobs!")


# @app.command()
# def samples(
#     ctx: typer.Context,
#     path_out: str = typer.Argument("./tmp", help="Path to output directory."),
# ):
#     """Generate sample Work Orders and Jobs."""
#     output_path_string = validate_output_path(path_out)
#     output_path = Path(output_path_string) / Path("samples")
#     typer.echo(f"Samples will be saved to {output_path.resolve()}")
#     ewo_list = [
#         example_work_orders.response_to_job_json_file,
#         example_work_orders.result_to_job_json_file,
#         example_work_orders.result_to_json_file_and_response_to_json_file,
#         example_work_orders.result_and_response_to_job_json_file,
#         example_work_orders.result_to_json_file,
#         example_work_orders.result_to_csv_file,
#         example_work_orders.result_with_pages_to_json_file,
#     ]
#     for sample in ewo_list:
#         ewo_: EsiWorkOrder = sample()
#         file_path = (
#             output_path / Path("work-orders") / Path(ewo_.name).with_suffix(".json")
#         )
#         ewo_string = serialize_work_order(ewo_)
#         save_string(ewo_string, file_path, parents=True)
#     jobs_list: Sequence[Callable] = [
#         example_jobs.get_industry_facilities,
#         example_jobs.get_industry_systems,
#         example_jobs.post_universe_names,
#     ]
#     default_callbacks = DefaultCallbackProvider().default_callback_collection()
#     for sample in jobs_list:
#         job: EsiJob = sample(default_callbacks)
#         file_path = output_path / Path("jobs") / Path(job.name).with_suffix(".json")
#         job_string = serialize_job(job)
#         save_string(job_string, file_path, parents=True)
#     start = ctx.obj.get("start_time", perf_counter_ns())
#     end = perf_counter_ns()
#     seconds = (end - start) / 1000000000
#     typer.echo(f"Task completed in {seconds:0.2f} seconds")


# def combine(ctx: typer.Context, source_path: Path, out_path: Path):
#     """combine all the jobs in a dir into one workorder."""
#     pass


# def bulk_create(ctx: typer.Context, op_id, input_file: Path, file_type: str):
#     """Bulk create jobs from json or csv files.

#     json must be in list of dicts of valid params for op_id
#     csv must read into a list of dicts that contain the required params
#     extra params are ok.
#     should be able to read previous csv output that contains required fields
#     identical inputs will be consolidated. (dict to json.dumps, set, and back)
#     """
#     pass
