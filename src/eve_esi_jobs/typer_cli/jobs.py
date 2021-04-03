"""Running work orders"""

import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Optional

import typer

from eve_esi_jobs import sample_work_orders
from eve_esi_jobs.eve_esi_jobs import deserialize_work_order_from_dict, do_work_order
from eve_esi_jobs.typer_cli.cli_helpers import (
    load_esi_work_order_json,
    save_json,
    validate_input_path,
    validate_output_path,
)

app = typer.Typer(help="""Work with Esi Jobs and Work Orders.\n\nmore info.""")
logger = logging.getLogger(__name__)


@app.command()
def run(
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
    """Load work orders and run them.

    Dry-run will perform all operations up to but not including making the actual
    http requests. This will detect some missed settings and parameters, but does
    not find mistakes that can only be checked on the server, eg. a non-existant type_id.
    """

    if dry_run:
        typer.BadParameter("not implemented yet.")
    template_overrides = {}
    path_in = validate_input_path(path_in)
    esi_work_order_json = load_esi_work_order_json(Path(path_in))
    esi_work_order = deserialize_work_order_from_dict(esi_work_order_json)
    if path_out is not None:
        path_out = validate_output_path(path_out)
        output_path_string = str(path_out / Path(esi_work_order.parent_path_template))
        template_overrides["ewo_parent_path_template"] = output_path_string
    esi_work_order.add_template_overrides(template_overrides)
    esi_provider = ctx.obj["esi_provider"]
    do_work_order(esi_work_order, esi_provider)
    typer.echo(f"Completed {len(esi_work_order.jobs)} jobs!")
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")


@app.command()
def samples(
    ctx: typer.Context,
    path_out: str = typer.Argument(..., help="Path to output directory."),
):
    """"""
    output_path_string = validate_output_path(path_out)
    output_path = Path(output_path_string) / Path("samples")
    sample_list = [
        sample_work_orders.response_to_job_json_file,
        sample_work_orders.result_to_job_json_file,
        sample_work_orders.result_to_json_file_and_response_to_json_file,
        sample_work_orders.result_and_response_to_job_json_file,
        sample_work_orders.result_to_json_file,
        sample_work_orders.result_to_csv_file,
    ]
    typer.echo(f"Sample Esi Work Orders will be saved to {output_path.resolve()}")
    for sample in sample_list:
        ewo = sample()
        file_path = output_path / Path(ewo.name).with_suffix(".json")
        save_json(ewo.dict(), file_path, parents=True)
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")


def combine(ctx: typer.Context, source_path: Path, out_path: Path):
    """combine all the jobs in a dir into one workorder."""
    pass


def bulk_create(ctx: typer.Context, op_id, input_file: Path, file_type: str):
    """Bulk create jobs from json or csv files.

    json must be in list of dicts of valid params for op_id
    csv must read into a list of dicts that contain the required params
    extra params are ok.
    should be able to read previous csv output that contains required fields
    identical inputs will be consolidated. (dict to json.dumps, set, and back)
    """
    pass
