from pathlib import Path
from typing import Dict, Optional

from eve_esi_jobs.models import EsiJob, EsiWorkOrder


def deserialize_json_job(esi_job_json: Dict) -> EsiJob:
    esi_job = EsiJob(**esi_job_json)
    return esi_job


def deserialize_json_work_order(esi_work_order_json: Dict) -> EsiWorkOrder:
    esi_work_order = EsiWorkOrder(**esi_work_order_json)
    return esi_work_order


def add_parent_path(esi_work_order: EsiWorkOrder, parent_path_override: Optional[Path]):
    """work order pre processor. preprocessors should include override option to allow outside modification. ie cli override"""
    if parent_path_override is not None:
        parent_path = parent_path_override
    else:
        parent_path = esi_work_order.parent_path
    for esi_job in esi_work_order.jobs:
        for callback in esi_job.callback_iter():
            if callback.callback_id == "save_json_to_file":
                full_path = parent_path / Path(callback.kwargs["file_path"])
                callback.kwargs["file_path"] = full_path
