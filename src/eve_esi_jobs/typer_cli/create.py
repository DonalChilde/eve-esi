import csv
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

import typer

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.eve_esi_jobs import (
    deserialize_job_from_string,
    deserialize_work_order_from_string,
    serialize_job,
    serialize_work_order,
)
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import CallbackCollection, EsiJob, EsiWorkOrder, JobCallback
from eve_esi_jobs.typer_cli.cli_helpers import (  # load_job,
    check_for_op_id,
    completion_op_id,
    report_finished_task,
    save_string,
)

app = typer.Typer(help="Create Jobs and Workorders")
logger = logging.getLogger(__name__)

DEFAULT_WORKORDER = EsiWorkOrder(
    output_path="workorders/${ewo_iso_date_time}/workorder-${ewo_uid}"
)


@app.command()
def ewo(
    ctx: typer.Context,
    path_in: Path = typer.Argument(...),
    path_out: Path = typer.Argument(...),
    file_name: Path = typer.Option(
        "workorders/${ewo_iso_date_time}/workorder-${ewo_uid}.json",
        "-f",
        "--file-name",
        help="file name for the work order. Can include directories.",
    ),
    ewo_path: Optional[Path] = typer.Option(None, "-w", "--work-order"),
):
    """Create a Workorder, and add existing jobs to it.

    Can also add jobs to an existing Workorder.
    """
    _ = ctx
    # TODO change ewo_string to a json file path
    if not path_in.exists():
        raise typer.BadParameter(f"{path_in} does not exist.")
    loaded_jobs = []
    if path_in.is_file():
        job_string = path_in.read_text()
        loaded_job = deserialize_job_from_string(job_string, format_id="json")
        if loaded_job is not None:
            loaded_jobs.append(loaded_job)
    if path_in.is_dir():
        maybe_jobs = path_in.glob("*.json")
        for maybe_job in maybe_jobs:
            job_string = maybe_job.read_text()
            loaded_job = deserialize_job_from_string(job_string, format_id="json")
            # if loaded_job is not None:
            loaded_jobs.append(loaded_job)
    if not loaded_jobs:
        raise typer.BadParameter(f"No jobs found at {path_in}")
    if ewo_path is None:
        # TODO change this?
        ewo_ = DEFAULT_WORKORDER.copy()
    else:
        try:
            ewo_string = ewo_path.read_text()
            ewo_ = deserialize_work_order_from_string(ewo_string)
        except Exception as ex:
            raise typer.BadParameter(
                f"Error decoding work order string. {ex.__class__.__name__}, {ex}"
            )
    ewo_.jobs.extend(loaded_jobs)
    output_path = path_out / file_name
    out_template = Template(str(output_path))
    out_string = out_template.substitute(ewo_.attributes())
    out_path_from_template = Path(out_string)
    try:
        save_string(serialize_work_order(ewo_), out_path_from_template, parents=True)
        typer.echo(f"Workorder saved to {out_path_from_template}")
        report_finished_task(ctx)
    except Exception as ex:
        raise typer.BadParameter(
            f"Error saving work order to {path_out}. {ex.__class__.__name__}, {ex}"
        )


@app.command()
def jobs(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ...,
        autocompletion=completion_op_id,
        callback=check_for_op_id,
        help="A valid op-id.",
    ),
    param_string: Optional[str] = typer.Option(
        None,
        "--param-string",
        "-p",
        help="Optional. Full or partial parameters as a json string.",
    ),
    callback_path: Optional[Path] = typer.Option(
        None,
        "-c",
        "--callbacks",
        help="Optional. Json file of callbacks to be used. ",
    ),
    file_name_template: str = typer.Option(
        "created-jobs/${esi_job_op_id}-${esi_job_uid}.json",
        "-n",
        "--job-name",
        help="Optional. Customize template used for job file name.",
    ),
    data_path: Optional[Path] = typer.Option(
        None,
        "--data-file",
        "-i",
        help=(
            "Optional. Path to json or csv file with full or partial parameters. "
            "Must result in a list of dicts."
        ),
    ),
    path_out: Path = typer.Argument(..., help="Output directory."),
):
    """Create one or more jobs from an op_id.

    Required parameters can be supplied as a combination of param-string and file-data.

    This allows supplying one region_id through param-string,
    and a list of type_ids from a csv file to get multiple jobs.

    Csv files must have properly labeled columns.
    """
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    path_out = optional_object(path_out, Path, ".")
    if path_out.is_file:
        typer.BadParameter("path_out must not be a file.")
    file_data: Optional[List[Dict]] = get_params_from_file(data_path)
    parameters: Dict = decode_param_string(param_string)
    if callback_path is None:
        callback_collection = default_callback_collection()
    else:
        callback_collection = load_callbacks(callback_path)
    jobs_ = []
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
        file_path = resolve_job_file_path(job, file_name_template, path_out)
        job_string = serialize_job(job)
        save_string(job_string, file_path, parents=True)
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
            file_data = load_json_or_csv(file_path)
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
        callback_collection_string = file_path.read_text()
        callback_collection_json = json.loads(callback_collection_string)
        callback_collection = CallbackCollection(**callback_collection_json)
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


def load_json_or_csv(file_path: Path):
    if file_path.suffix.lower() not in [".json", ".csv"]:
        raise typer.BadParameter(
            (
                f"{file_path} does not have a recognized file type "
                "suffix. Should be either .json or .csv."
            )
        )
    with open(file_path) as file:
        if file_path.suffix.lower() == ".json":
            data = json.load(file)
            return data
        if file_path.suffix.lower() == ".csv":
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
            return data


def default_callback_collection() -> CallbackCollection:
    callback_collection = CallbackCollection()
    callback_collection.success.append(
        JobCallback(callback_id="response_content_to_json")
    )
    callback_collection.success.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.success.append(
        JobCallback(
            callback_id="save_json_result_to_file",
            kwargs={"file_path": "job_data/${esi_job_op_id}-${esi_job_uid}.json"},
        )
    )
    callback_collection.fail.append(JobCallback(callback_id="response_to_esi_job"))
    callback_collection.fail.append(JobCallback(callback_id="log_job_failure"))
    return callback_collection
