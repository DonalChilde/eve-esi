import logging
from pathlib import Path
from typing import Callable, Sequence

import typer

from eve_esi_jobs import models
from eve_esi_jobs.examples import callback_collections as example_callbacks
from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.examples import work_orders as example_work_orders
from eve_esi_jobs.model_helpers import default_callback_collection
from eve_esi_jobs.models import EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (
    report_finished_task,
    validate_output_path,
)

app = typer.Typer(help="""Save examples to file.""")
logger = logging.getLogger(__name__)


@app.command()
def all_examples(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to example output directory."),
):
    """Generate all examples."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("examples")
    typer.echo(f"Examples will be saved to {output_path.resolve()}")
    save_job_examples(output_path)
    save_work_order_examples(output_path)
    save_callback_examples(output_path)
    report_finished_task(ctx)


@app.command()
def workorders(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to example output directory."),
):
    """Generate example workorders."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("examples")
    typer.echo(f"Examples will be saved to {output_path.resolve()}")
    save_work_order_examples(output_path)
    report_finished_task(ctx)


@app.command()
def jobs(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to example output directory."),
):
    """Generate example jobs."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("examples")
    typer.echo(f"Examples will be saved to {output_path.resolve()}")
    save_job_examples(output_path)
    report_finished_task(ctx)


@app.command()
def callbacks(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to example output directory."),
):
    """Generate example callbacks."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("examples")
    typer.echo(f"Examples will be saved to {output_path.resolve()}")
    save_callback_examples(output_path)
    report_finished_task(ctx)


def save_callback_examples(output_path: Path):
    callbacks_list: Sequence[Callable] = [
        example_callbacks.no_file_output,
        example_callbacks.generic_save_result_to_json,
        example_callbacks.generic_save_result_and_job_to_separate_json,
        example_callbacks.generic_save_result_and_job_to_same_json,
    ]
    for sample in callbacks_list:
        callback_collection: models.CallbackCollection = sample()
        file_path = output_path / Path("callbacks") / Path(sample.__name__)
        callback_collection.serialize_file(file_path, "json")
        callback_collection.serialize_file(file_path, "yaml")


def save_job_examples(output_path: Path):
    jobs_list: Sequence[Callable] = [
        example_jobs.get_industry_facilities,
        example_jobs.get_industry_systems,
        example_jobs.post_universe_names,
    ]
    default_callbacks = default_callback_collection()
    for sample in jobs_list:
        job: EsiJob = sample(default_callbacks)
        file_path = output_path / Path("jobs") / Path(job.name)
        job.serialize_file(file_path, "json")
        job.serialize_file(file_path, "yaml")


def save_work_order_examples(output_path: Path):
    ewo_list = [
        example_work_orders.example_workorder,
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
        file_path = output_path / Path("work-orders") / Path(ewo_.name)
        ewo_.serialize_file(file_path, "json")
        ewo_.serialize_file(file_path, "yaml")
