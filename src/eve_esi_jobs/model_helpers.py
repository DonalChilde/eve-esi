import logging
from pathlib import Path
from typing import Dict, Optional

from eve_esi_jobs.helpers import combine_dictionaries
from eve_esi_jobs.models import EsiJob, EsiWorkOrder

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class WorkOrderPreprocessor:
    def __init__(self) -> None:
        pass

    def pre_process_work_order(self, ewo: EsiWorkOrder):
        for esi_job in ewo.jobs:
            self._add_file_path_prefix_to_callbacks(esi_job, ewo.attributes())

    def _add_file_path_prefix_to_callbacks(
        self, esi_job: EsiJob, template_overrides: Optional[Dict[str, str]] = None
    ):
        if template_overrides is not None:
            template_values = combine_dictionaries(
                esi_job.attributes(), [template_overrides]
            )
        else:
            template_values = esi_job.attributes()
        parent_path: str = template_values.get("ewo_parent_path_template", "")
        for callback in esi_job.callback_iter():
            file_path = callback.kwargs.get("file_path", None)
            if file_path is not None:
                full_path_string = str(Path(parent_path) / Path(file_path))
                callback.kwargs["file_path"] = full_path_string
                logger.info("file_path: %s", full_path_string)
