import csv
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

import typer

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.eve_esi_jobs import serialize_job
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import CallbackCollection, EsiJob
from eve_esi_jobs.typer_cli.cli_helpers import (
    check_for_op_id,
    completion_op_id,
    save_string,
)

app = typer.Typer(help="Create Jobs")
logger = logging.getLogger(__name__)

DEFAULT_CALLBACK_STRING = """
    {
      "success": [
       {
        "callback_id": "response_content_to_json"
       },
       {
        "callback_id": "save_json_result_to_file",
        "kwargs": {
         "file_path": "job_data/${esi_job_op_id}-${esi_job_uid}.json"
        }
       }
      ]
     }
     """


@app.command()
def from_op_id(
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
    callback_string: Optional[str] = typer.Option(
        None,
        "-c",
        "--callbacks",
        help=(
            "Optional. Specify callbacks to be used. "
            "Defaults to saving json data to file."
        ),
    ),
    file_name_template: str = typer.Option(
        "created-jobs/${esi_job_op_id}-${esi_job_uid}.json",
        "-n",
        "--job-name",
        help="Optional. Customize template used for job file name.",
    ),
    path_in: Optional[Path] = typer.Option(
        None,
        "--file-data",
        "-i",
        help=(
            "Optional. Path to json or csv file with full or partial parameters. "
            "Must result in a list of dicts."
        ),
    ),
    path_out: Optional[Path] = typer.Option(".", "--jobs-out", "-o"),
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
    file_data: Optional[List[Dict]] = get_params_from_file(path_in)
    parameters: Dict = decode_param_string(param_string)
    callbacks: Optional[CallbackCollection] = check_for_callbacks(callback_string)
    if not file_data:
        job = create_job(op_id, parameters, callbacks, esi_provider)
        if validate_job(job, esi_provider):
            save_job(job, file_name_template, path_out)
    else:
        for params in file_data:
            params.update(parameters)
            job = create_job(op_id, params, callbacks, esi_provider)
            if validate_job(job, esi_provider):
                save_job(job, file_name_template, path_out)


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


def check_for_callbacks(callback_string: Optional[str]) -> Optional[CallbackCollection]:
    if callback_string is not None:
        try:
            callback_dict = json.loads(callback_string)
            callbacks = CallbackCollection(**callback_dict)
            return callbacks
        except Exception as ex:
            raise typer.BadParameter(
                f"Error decoding callback string. {ex.__class__.__name__}, {ex}"
            )
    return None


def create_job(
    op_id: str,
    parameters: Dict,
    callbacks: Optional[CallbackCollection],
    esi_provider: EsiProvider,
):

    if not check_required_params(op_id, parameters, esi_provider):
        raise typer.BadParameter(
            f"Missing required parameters for {op_id}, was given {parameters}"
        )
    filtered_params = filter_extra_params(op_id, parameters, esi_provider)
    default_json = json.loads(DEFAULT_CALLBACK_STRING)
    default_callbacks = CallbackCollection(**default_json)

    if callbacks is not None:
        job_callbacks = callbacks
    else:
        job_callbacks = default_callbacks

    job_dict = {
        "op_id": op_id,
        "name": "",
        "parameters": filtered_params,
        "callbacks": job_callbacks,
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


def save_job(job: EsiJob, file_path_template: str, path_out: Path):
    template_args = job.attributes()
    combined_template_string = str(Path(path_out) / Path(file_path_template))
    template = Template(combined_template_string)
    file_path_string = template.substitute(template_args)
    file_path = Path(file_path_string)
    job_string = serialize_job(job)
    save_string(job_string, file_path, parents=True)
    logger.info("Saved job %s at %s", job.uid, file_path)


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
