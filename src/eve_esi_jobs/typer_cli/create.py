import csv
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

import typer
import yaml

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.models import CallbackCollection, EsiJob, EsiWorkOrder
from eve_esi_jobs.typer_cli.cli_helpers import (
    FormatChoices,
    check_for_op_id,
    completion_op_id,
    default_callback_collection,
    report_finished_task,
    save_string,
)

app = typer.Typer(help="Create jobs and workorders")
logger = logging.getLogger(__name__)


@app.command()
def workorder(
    ctx: typer.Context,
    path_in: Path = typer.Argument(
        ...,
        help="Path to the job file(s).",
    ),
    path_out: Path = typer.Argument(
        "./tmp",
        help="Parent path for saving the new workorder, will be prepended to --file-name.",
    ),
    format_id: FormatChoices = typer.Option(
        FormatChoices.json,
        "-f",
        "--format-id",
        show_choices=True,
        help="Output file format.",
    ),
    file_name: Path = typer.Option(
        "workorders/${ewo_iso_date_time}/workorder-${ewo_uid}",
        "-n",
        "--file-name",
        help=(
            "File name for the new workorder. Can include directories, "
            "and the file type suffix will be added based on --format-id if necessary."
        ),
    ),
    ewo_path: Optional[Path] = typer.Option(
        None,
        "-w",
        "--existing-work-order",
        help="Path to an existing workorder.",
    ),
):
    """Create a workorder, and add existing jobs to it.

    Can also add jobs to an existing Workorder.
    """
    _ = ctx
    if not path_in.exists():
        raise typer.BadParameter(f"{path_in} does not exist.")
    if path_in.is_file():
        maybe_jobs = [path_in]
    else:
        maybe_jobs = [*path_in.glob("*.json"), *path_in.glob("*.yaml")]
    loaded_jobs = []
    for maybe_job in maybe_jobs:
        try:
            loaded_job = EsiJob.deserialize_file(maybe_job)
        except Exception as ex:
            raise typer.BadParameter(f"Error decoding job at {maybe_job}, msg:{ex}")
        loaded_jobs.append(loaded_job)
    if not loaded_jobs:
        raise typer.BadParameter(f"No jobs found at {path_in}")
    if ewo_path is None:
        ewo_ = get_default_workorder()
    else:
        try:
            ewo_ = EsiWorkOrder.deserialize_file(ewo_path)
        except Exception as ex:
            raise typer.BadParameter(
                f"Error decoding workorder string. {ex.__class__.__name__}, {ex}"
            )
    ewo_.jobs.extend(loaded_jobs)
    output_path = path_out / file_name
    out_template = Template(str(output_path))
    file_path = Path(out_template.substitute(ewo_.attributes()))
    try:
        saved_path = ewo_.serialize_file(file_path, format_id)
        typer.echo(f"Workorder saved to {saved_path}")
        report_finished_task(ctx)
    except Exception as ex:
        raise typer.BadParameter(
            f"Error saving workorder to {path_out}. {ex.__class__.__name__}, {ex}"
        )


@app.command()
def jobs(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ...,
        autocompletion=completion_op_id,
        callback=check_for_op_id,
        help="A valid op-id. e.g. get_markets_prices",
    ),
    param_string: Optional[str] = typer.Option(
        None,
        "--param-string",
        "-p",
        help="Optional. Full or partial parameters as a json encoded dictionary string. "
        "Keys must be valid parameters for selected op_id.",
    ),
    callback_path: Optional[Path] = typer.Option(
        None,
        "-c",
        "--callbacks",
        help="Optional. Path to custom callbacks to be used. ",
    ),
    file_name: str = typer.Option(
        "created-jobs/${esi_job_op_id}-${esi_job_uid}",
        "-n",
        "--file-name",
        help=(
            "File name for the new job, must be unique if multiple jobs. "
            "Can include directories, "
            "and the file type suffix will be added based on --format-id."
        ),
    ),
    data_path: Optional[Path] = typer.Option(
        None,
        "--data-file",
        "-i",
        help=(
            "Optional. Path to json, csv, or yaml file with full or partial parameters. "
            "Must result in a list of dicts."
        ),
    ),
    format_id: FormatChoices = typer.Option(
        FormatChoices.json,
        "-f",
        "--format-id",
        show_choices=True,
        help="Output file format.",
    ),
    path_out: Path = typer.Argument(
        "./tmp",
        help="Parent path for saving the new jobs, will be prepended to --file-name.",
    ),
):
    """Create one or more jobs from an op_id.

    Required parameters can be supplied as a combination of --param-string and file data.

    This allows supplying one region_id through param-string,
    and a list of type_ids from a csv file to get multiple jobs.

    Csv input files must have properly labeled columns.
    """
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    # path_out = optional_object(path_out, Path, ".")
    if path_out.is_file:
        typer.BadParameter("path_out must not be a file.")
    file_data: Optional[List[Dict]] = get_params_from_file(data_path)
    parameters: Dict = decode_param_string(param_string)
    if callback_path is None:
        callback_collection = default_callback_collection()
    else:
        callback_collection = load_callbacks(callback_path)
    jobs_: List[EsiJob] = []
    if not file_data:
        job = create_job(op_id, parameters, callback_collection, esi_provider)
        jobs_.append(job)
    else:
        for params in file_data:
            params.update(parameters)
            job = create_job(op_id, params, callback_collection, esi_provider)
            jobs_.append(job)
    # validate jobs
    for job in jobs_:
        file_path = resolve_job_file_path(job, file_name, path_out)
        try:
            save_path = job.serialize_file(file_path, format_id)
        except Exception as ex:
            raise typer.BadParameter(
                f"Error saving job to {save_path}. {ex.__class__.__name__}, {ex}"
            )
        save_string(job.serialize_json(), file_path, parents=True)
        logger.info("Saved job %s at %s", job.uid, file_path)
    typer.echo(f"{len(jobs_)} jobs saved to {path_out}")
    report_finished_task(ctx)


def decode_param_string(param_string: Optional[str]) -> Dict:
    if param_string is None:
        return {}
    try:
        parameters = json.loads(param_string)
        return parameters
    except json.decoder.JSONDecodeError as ex:
        raise typer.BadParameter(
            f"{param_string} is not a valid json string. msg: {ex}"
        )


def get_params_from_file(file_path: Optional[Path]) -> Optional[List[Dict]]:

    if file_path is not None:
        if file_path.is_file():
            file_data = load_data_file(file_path)
            if not isinstance(file_data, list):
                raise typer.BadParameter(f"{file_path} is not a list of dicts. 1")
            if not file_data:
                raise typer.BadParameter(f"{file_path} had no data.")
            if not isinstance(file_data[0], dict):
                raise typer.BadParameter(f"{file_path} is not a list of dicts.")
            return file_data
        raise typer.BadParameter(f"{file_path} is not a file.")
    return None


def load_callbacks(file_path: Path) -> CallbackCollection:
    try:
        callback_collection = CallbackCollection.deserialize_file(file_path)
        return callback_collection
    except Exception as ex:
        raise typer.BadParameter(
            f"Error decoding callback string. {ex.__class__.__name__}, {ex}"
        )


def create_job(
    op_id: str,
    parameters: Dict,
    callbacks: CallbackCollection,
    esi_provider: EsiProvider,
):

    if not check_required_params(op_id, parameters, esi_provider):
        raise typer.BadParameter(
            f"Missing required parameters for {op_id}, was given {parameters}"
        )
    filtered_params = filter_extra_params(op_id, parameters, esi_provider)
    job_dict = {
        "op_id": op_id,
        "name": "",
        "parameters": filtered_params,
        "callbacks": callbacks,
    }
    job = EsiJob(**job_dict)

    return job


def check_required_params(op_id, parameters, esi_provider: EsiProvider) -> bool:
    """check that required params are present"""
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        raise typer.BadParameter(f"op_id: {op_id} does not exist.")
    required_params = [
        param
        for param in op_id_info.parameters.values()
        if param.get("required", False)
    ]
    for item in required_params:
        name = item.get("name")
        if name not in parameters:
            return False
    return True


def filter_extra_params(
    op_id: str, parameters: Dict, esi_provider: EsiProvider
) -> Dict:
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        raise typer.BadParameter(f"op_id: {op_id} does not exist.")
    legal_parameter_names: List[str] = list(op_id_info.parameters.keys())
    filtered_params = {}
    for name in legal_parameter_names:
        if name in parameters:
            filtered_params[name] = parameters[name]
    return filtered_params


def validate_job(job: EsiJob, esi_provider):
    _, _ = job, esi_provider
    return True


def resolve_job_file_path(job: EsiJob, file_path_template: str, path_out: Path):
    template_args = job.attributes()
    combined_template_string = str(Path(path_out) / Path(file_path_template))
    template = Template(combined_template_string)
    file_path_string = template.substitute(template_args)
    file_path = Path(file_path_string)
    return file_path


def load_data_file(file_path: Path):
    valid_suffixes = [".json", ".csv", ".yaml"]
    if file_path.suffix.lower() not in valid_suffixes:
        raise typer.BadParameter(
            (
                f"{file_path} does not have a recognized file type "
                f"suffix. Should be one of {valid_suffixes}"
            )
        )
    with open(file_path) as file:
        if file_path.suffix.lower() == ".json":
            data = json.load(file)
            return data
        if file_path.suffix.lower() == ".yaml":
            data = yaml.safe_load(file)
            return data
        if file_path.suffix.lower() == ".csv":
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
            return data


def get_default_workorder():
    ewo = EsiWorkOrder(
        output_path="workorders/${ewo_iso_date_time}/workorder-${ewo_uid}"
    )
    return ewo
