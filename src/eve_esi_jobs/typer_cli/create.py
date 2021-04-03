import csv
import dataclasses
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, List, Optional
from uuid import uuid4

import typer
import yaml
from rich import inspect

from eve_esi_jobs import callbacks as EJC
from eve_esi_jobs.esi_provider import EsiProvider, OpIdLookup
from eve_esi_jobs.eve_esi_jobs import serialize_job, serialize_work_order
from eve_esi_jobs.helpers import optional_object
from eve_esi_jobs.models import CallbackCollection, EsiJob, JobCallback
from eve_esi_jobs.typer_cli.cli_helpers import (
    check_for_op_id,
    completion_op_id,
    save_json,
    save_string,
    validate_output_path,
)

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.command()
def from_op_id(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ..., autocompletion=completion_op_id, callback=check_for_op_id
    ),
    param_string: Optional[str] = typer.Option(None, "--param_string", "-p"),
    callbacks: Optional[str] = typer.Option(None),
    file_name_template: Optional[str] = typer.Option(None),
    path_in: Optional[Path] = typer.Option(None),
    path_out: Optional[Path] = typer.Option(None),
    # explain: bool = typer.Option(False, "--explain", "-e"),
    # create: bool = typer.Option(False, "--create", "-c"),
):
    """Create a job from op_id and json string

    options - create, explain maybe if not create then explain?
    """
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    path_out = optional_object(path_out, Path, ".")
    if path_out.is_file:
        typer.BadParameter("path_out must not be a file.")
    # op_id_info = esi_provider.op_id_lookup[op_id]
    if file_name_template is None:
        file_name_template = "created_jobs/${esi_job_op_id}-${esi_job_id}.json"
    file_data = []
    string_params = {}
    if path_in is not None:
        path_to_file = Path(path_in)
        if path_to_file.is_file():
            file_data = load_json_or_csv(path_to_file)
        else:
            typer.BadParameter(f"{path_in} is not a file.")
    if param_string is not None:
        string_params = json.loads(param_string)
    if not file_data:
        job = create_job(op_id, string_params, callbacks, esi_provider)
        if validate_job(job, esi_provider):
            save_job(job, file_name_template, path_out)
    # get params from op_id
    # get data from file
    #   - valid types:
    #       - csv with headers
    #       - json list of dicts
    # for each dict from file, combine with provided params.

    # build job
    # save job {op_id}{uuid}.json or template
    # option for job file name template


def create_job(
    op_id, parameters, callback_config: Optional[str], esi_provider: EsiProvider
):
    """
    [summary]

    [extended_summary]

    Args:
        op_id ([type]): [description]
        parameters ([type]): [description]
        callback_config ([type]): [description]
        esi_provider ([type]): [description]

    Raises:
        typer.BadParameter: [description]

    Returns:
        [type]: [description]
    """
    if not check_required_params(op_id, parameters, esi_provider):
        raise typer.BadParameter(
            f"Missing required parameters for {op_id}, was given {parameters}"
        )
    filtered_params = filter_extra_params(op_id, parameters, esi_provider)
    callback_json = {
        "success": [
            {"callback_id": "response_content_to_json"},
            {
                "callback_id": "save_json_result_to_file",
                "kwargs": {
                    "file_path": "job_data/${esi_job_op_id}-${esi_job_uid}.json"
                },
            },
        ]
    }

    job_dict = {
        "op_id": op_id,
        "name": "",
        # "id_": str(uuid4()),
        "parameters": filtered_params,
        "result_callbacks": callback_json,
    }
    job = EsiJob(**job_dict)
    # TODO remove unneccessary params
    # TODO get default callback args, eg. file_path
    return job


def check_required_params(op_id, parameters, esi_provider: EsiProvider) -> bool:
    """check that required params are present"""
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        raise typer.BadParameter(f"op_id: {op_id} does not exist.")

    # inspect(op_id_info.parameters)
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
    return True


def save_job(job: EsiJob, file_path_template: str, path_out: Path):
    template_args = job.get_template_overrides()
    # if path_out.is_dir():
    #     # path_out = validate_output_path(str(path_out))
    combined_template_string = str(Path(path_out) / Path(file_path_template))
    # else:
    #     combined_template_string = file_path_template
    template = Template(combined_template_string)
    file_path_string = template.substitute(template_args)
    file_path = Path(file_path_string)
    job_string = serialize_job(job)
    save_string(job_string, file_path, parents=True)
    logger.info(f"Saved job {job.uid} at {file_path}")


def load_json_or_csv(file_path: Path):
    if file_path.suffix.lower() not in ["json", "cssv"]:
        raise typer.BadParameter(
            (
                f"{file_path} does not have a recognized file type "
                "suffix. Should be either .json or .csv."
            )
        )
    with open(file_path) as file:
        if file_path.suffix.lower() == "json":
            data = json.load(file)
            return data
        if file_path.suffix.lower() == "csv":
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
            return data


# def explain_out(op_id, esi_provider: EsiProvider):
#     op_id_info: Optional[OpIdLookup] = esi_provider.op_id_lookup.get(op_id, None)
#     if op_id_info is None:
#         typer.BadParameter(f"{op_id} is not Valid.")
#     typer.echo(yaml.dump(dataclasses.asdict(op_id_info)))
#     # possible_parameters = op_id_info.parameters
#     # successful_response = op_id_info.response
#     # typer.echo(f"op_id: {op_id}")
#     # typer.echo(f"possible parameters: \n{yaml.dump(possible_parameters)}")
#     # # typer.echo(f"possible parameters: {json.dumps(possible_parameters,indent=1)}")
#     # typer.echo(f"returns: \n{yaml.dump(successful_response)}")
