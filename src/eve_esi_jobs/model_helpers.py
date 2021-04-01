import logging
from pathlib import Path
from string import Template
from typing import Dict, Optional

from rich import inspect

from eve_esi_jobs.helpers import combine_dictionaries
from eve_esi_jobs.models import EsiJob, EsiWorkOrder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# def resolve_file_callback_path_template(
#     esi_job: EsiJob, template_overrides: Optional[Dict[str, str]] = None
# ):
#     """Turn a template into a file path for callbacks.

#     Check :func:`JobCallback`.config for a `file_path_template` entry,
#     process the template and update the kwargs for the callback.

#     Args:
#         esi_job: A job with callbacks to check.
#         template_overrides: A dict of values to override those found
#             in the :class:`EsiJob`. Defaults to None.
#     """
#     # FIXME test with empty ewo_parent_path_template
#     if template_overrides is not None:
#         template_values = combine_dictionaries(
#             esi_job.get_template_overrides(), [template_overrides]
#         )
#     else:
#         template_values = esi_job.get_template_overrides()
#     parent_path: str = template_values.get("ewo_parent_path_template", "")
#     # inspect(combined_params)
#     for callback in esi_job.callback_iter():
#         if callback.config is not None:
#             file_path_template = callback.config.get("file_path_template", None)
#             if file_path_template is not None:
#                 full_path_template_string = str(
#                     Path(parent_path) / Path(file_path_template)
#                 )
#                 # template = Template(full_path_template_string)
#                 # resolved_string = template.substitute(template_values)
#                 # callback.kwargs["file_path"] = resolved_string
#                 callback.kwargs["file_path"] = full_path_template_string
#                 # inspect(callback)


def add_file_path_prefix_to_callbacks(
    esi_job: EsiJob, template_overrides: Optional[Dict[str, str]] = None
):
    if template_overrides is not None:
        template_values = combine_dictionaries(
            esi_job.get_template_overrides(), [template_overrides]
        )
    else:
        template_values = esi_job.get_template_overrides()
    parent_path: str = template_values.get("ewo_parent_path_template", "")
    for callback in esi_job.callback_iter():
        file_path = callback.kwargs.get("file_path", None)
        if file_path is not None:
            full_path_string = str(Path(parent_path) / Path(file_path))
            callback.kwargs["file_path"] = full_path_string
            logger.info("file_path: %s", full_path_string)


def pre_process_work_order(ewo: EsiWorkOrder):
    for esi_job in ewo.jobs:
        pre_process_job(esi_job, ewo.get_template_overrides())


def pre_process_job(esi_job: EsiJob, template_overrides: Dict):
    # esi_job.add_template_overrides(override_params)
    # resolve_file_callback_path_template(esi_job, template_overrides)
    add_file_path_prefix_to_callbacks(esi_job, template_overrides)
