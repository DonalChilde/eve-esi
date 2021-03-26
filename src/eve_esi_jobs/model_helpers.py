from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Dict, Optional, Sequence

from rich import inspect

if TYPE_CHECKING:
    from eve_esi_jobs.models import EsiJob, EsiWorkOrder


def resolve_file_callback_path_template(
    esi_job: "EsiJob", overrides: Optional[Dict] = None
):
    if overrides is not None:
        combined_params = combine_dictionaries(esi_job.get_params(), [overrides])
    else:
        combined_params = esi_job.get_params()
    parent_path: str = combined_params.get("ewo_parent_path_template", "")
    for callback in esi_job.callback_iter():
        if callback.config is not None:
            file_path_template = callback.config.get("file_path_template", None)
            if file_path_template is not None:
                full_path_template_string = str(
                    Path(parent_path) / Path(file_path_template)
                )
                template = Template(full_path_template_string)
                resolved_string = template.substitute(combined_params)
                callback.kwargs["file_path"] = resolved_string
                # inspect(callback)


def pre_process_work_order(ewo: "EsiWorkOrder"):
    for esi_job in ewo.jobs:
        pre_process_job(esi_job, ewo.get_params())


def pre_process_job(esi_job: "EsiJob", override_params: Dict):
    resolve_file_callback_path_template(esi_job, override_params)


def combine_dictionaries(base_dict: dict, overrides: Optional[Sequence[Dict]]) -> Dict:
    # TODO move this to collection util - NB makes a new dict with optional overrides
    combined_dict: Dict = {}
    combined_dict.update(base_dict)
    if overrides is not None:
        for override in overrides:
            combined_dict.update(override)
    return combined_dict