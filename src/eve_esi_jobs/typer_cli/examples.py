import csv
import json
import logging
from pathlib import Path
from typing import Callable, Dict, List, Sequence

import typer
import yaml

from eve_esi_jobs import models
from eve_esi_jobs.examples import input_data as example_input_data
from eve_esi_jobs.examples import jobs as example_jobs
from eve_esi_jobs.examples import work_orders as example_work_orders
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
    save_input_data_examples(output_path)
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
def input_data(
    ctx: typer.Context,
    path_out: str = typer.Argument("./tmp", help="Path to example output directory."),
):
    """Generate example input data."""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("examples")
    typer.echo(f"Examples will be saved to {output_path.resolve()}")
    report_finished_task(ctx)


def save_input_data_examples(output_path: Path):
    input_list: Sequence[Callable] = [
        example_input_data.market_history_params,
        example_input_data.market_history_params_extras,
        example_input_data.type_ids,
        example_input_data.region_ids,
    ]
    parent_path = output_path / Path("input-data")
    for sample in input_list:
        data = sample()
        file_path = parent_path / Path(sample.__name__)
        csv_path = file_path.with_suffix(".csv")
        save_csv(csv_path, data)
        yaml_path = file_path.with_suffix(".yaml")
        yaml_path.write_text(yaml.dump(data, sort_keys=False))
        json_path = file_path.with_suffix(".json")
        json_path.write_text(json.dumps(data, indent=2))
    return parent_path


def save_job_examples(output_path: Path):
    jobs_list: Sequence[Callable] = [
        example_jobs.get_industry_facilities,
        example_jobs.get_industry_systems,
        example_jobs.post_universe_names,
    ]

    parent_path = output_path / Path("jobs")
    for sample in jobs_list:
        job: EsiJob = sample()
        file_path = parent_path / Path(job.name)
        job.serialize_file(file_path, "json")
        job.serialize_file(file_path, "yaml")
    return parent_path


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
    parent_path = output_path / Path("workorders")
    for sample in ewo_list:
        ewo_: EsiWorkOrder = sample()
        file_path = parent_path / Path(ewo_.name)
        ewo_.serialize_file(file_path, "json")
        ewo_.serialize_file(file_path, "yaml")
    return parent_path


def save_csv(file_path: Path, data: List[Dict]):
    if file_path.suffix.lower() != ".csv":
        file_path = file_path.with_suffix(".csv")
    field_names = list(data[0])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, field_names)
        writer.writeheader()
        writer.writerows(data)
