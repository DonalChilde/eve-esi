import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Callable, Sequence

import typer

from eve_esi_jobs.callback_manifest import DefaultCallbackProvider
from eve_esi_jobs.eve_esi_jobs import serialize_job, serialize_work_order
from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.examples import work_orders as example_work_orders
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (
    report_finished_task,
    save_string,
    validate_output_path,
)

app = typer.Typer(help="""Save examples to file.""")
logger = logging.getLogger(__name__)


@app.command()
def all_examples(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to output directory."),
):
    """Generate sample Work Orders and Jobs."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("samples")
    typer.echo(f"Samples will be saved to {output_path.resolve()}")
    save_job_examples(output_path)
    save_work_order_examples(output_path)
    report_finished_task(ctx)


@app.command()
def workorders(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to output directory."),
):
    """Generate sample workorders."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("samples")
    typer.echo(f"Samples will be saved to {output_path.resolve()}")
    save_work_order_examples(output_path)
    report_finished_task(ctx)


@app.command()
def jobs(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to output directory."),
):
    """Generate sample jobs."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("samples")
    typer.echo(f"Samples will be saved to {output_path.resolve()}")
    save_job_examples(output_path)
    report_finished_task(ctx)


def save_job_examples(output_path: Path):
    jobs_list: Sequence[Callable] = [
        example_jobs.get_industry_facilities,
        example_jobs.get_industry_systems,
        example_jobs.post_universe_names,
    ]
    default_callbacks = DefaultCallbackProvider().default_callback_collection()
    for sample in jobs_list:
        job: EsiJob = sample(default_callbacks)
        file_path = output_path / Path("jobs") / Path(job.name).with_suffix(".json")
        job_string = serialize_job(job)
        save_string(job_string, file_path, parents=True)


def save_work_order_examples(output_path: Path):
    ewo_list = [
        example_work_orders.response_to_job_json_file,
        example_work_orders.result_to_job_json_file,
        example_work_orders.result_to_json_file_and_response_to_json_file,
        example_work_orders.result_and_response_to_job_json_file,
        example_work_orders.result_to_json_file,
        example_work_orders.result_to_csv_file,
        example_work_orders.result_with_pages_to_json_file,
    ]
    for sample in ewo_list:
        ewo_: EsiWorkOrder = sample()
        file_path = (
            output_path / Path("work-orders") / Path(ewo_.name).with_suffix(".json")
        )
        ewo_string = serialize_work_order(ewo_)
        save_string(ewo_string, file_path, parents=True)
