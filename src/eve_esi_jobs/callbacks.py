import csv
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

import aiofiles
import yaml
from more_itertools import spy

from eve_esi_jobs.helpers import combine_dictionaries
from eve_esi_jobs.models import EsiJob

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# pylint: disable=[useless-super-delegation,no-self-use]


class EsiJobCallback:
    def __init__(self, job: EsiJob) -> None:
        self.job = job

    async def do_callback(self):
        raise NotImplementedError()


class SaveJobResultToTxtFile(EsiJobCallback):
    """ """

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: Optional[str] = ".txt",
    ) -> None:
        super().__init__(job)
        self.file_path: Optional[Path] = None
        self.mode = mode
        self.file_path_template = file_path_template
        self.file_ending = file_ending

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"file_path={self.file_path!r}, mode={self.mode!r}, "
            f"file_path_template={self.file_path_template!r}, "
            f"file_ending={self.file_ending!r}, job_attributes={self.job.attributes()!r}"
            ")"
        )

    def refine_path(self):
        """Refine the file path."""

        template = Template(str(self.file_path_template))
        resolved_string = template.safe_substitute(self.job.attributes())
        self.file_path = Path(resolved_string)
        if self.file_ending is not None:
            assert self.file_path is not None
            self.file_path = self.file_path.with_suffix(self.file_ending)

    def get_data(self) -> str:
        """expects job.result.data to be a string."""
        assert self.job.result is not None
        data = json.dumps(self.job.result.data)
        return data

    async def do_callback(self):
        self.refine_path()
        try:
            assert self.file_path is not None
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(
                str(self.file_path), mode=self.mode
            ) as file:  # type:ignore
                data = self.get_data()
                await file.write(data)
        except Exception as ex:
            logger.exception("Exception saving file with %r.", self)
            raise ex


class SaveJobResultToJsonFile(SaveJobResultToTxtFile):
    """ """

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: str = ".json",
    ) -> None:
        super().__init__(
            job=job,
            mode=mode,
            file_path_template=file_path_template,
            file_ending=file_ending,
        )

    def get_data(self) -> str:
        """expects job.result.data to be json."""
        assert self.job.result is not None
        json_data = json.dumps(self.job.result.data, indent=2)
        return json_data


class SaveJobResultToYamlFile(SaveJobResultToTxtFile):
    """ """

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: str = ".yaml",
    ) -> None:
        super().__init__(
            job=job,
            mode=mode,
            file_path_template=file_path_template,
            file_ending=file_ending,
        )

    def get_data(self) -> str:
        """expects job.result.data to be json."""
        assert self.job.result is not None
        yaml_data = yaml.dump(self.job.result.data, sort_keys=False)
        return yaml_data


class SaveListOfDictResultToCSVFile(SaveJobResultToTxtFile):
    """Save the result to a CSV file.

    Expects the job.result.data to be a List[Dict].
    """

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: str = ".csv",
        field_names: Optional[List[str]] = None,
        additional_fields: Dict = None,
    ) -> None:
        super().__init__(
            job=job,
            mode=mode,
            file_path_template=file_path_template,
            file_ending=file_ending,
        )
        self.field_names = field_names
        self.additional_fields = additional_fields

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"file_path={self.file_path!r}, mode={self.mode!r}, "
            f"file_path_template={self.file_path_template!r}, "
            f"file_ending={self.file_ending!r}, job_attributes={self.job.attributes()!r}, "
            f"field_names={self.field_names!r}, additional_fields={self.additional_fields!r}, "
            ")"
        )

    def get_data(self) -> List[Dict]:  # type: ignore
        """expects job.result.data to be a List[Dict]."""
        assert self.job.result is not None
        assert self.job.result.data is list
        data: List[Dict] = self.job.result.data
        if self.additional_fields is not None:
            combined_data = []
            for item in data:
                combined_data.append(
                    combine_dictionaries(item, [self.additional_fields])
                )
            return combined_data
        return data

    async def do_callback(self):
        self.refine_path()
        try:
            assert self.file_path is not None
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            data = self.get_data()
            if self.field_names is None:
                first, data_iter = spy(data)
                self.field_names = list(first[0].keys())
                data = data_iter
            with open(str(self.file_path), mode=self.mode) as file:
                writer = csv.DictWriter(file, fieldnames=self.field_names)
                writer.writeheader()
                for item in data:
                    writer.writerow(item)
        except Exception as ex:
            logger.exception("Exception saving file with %r.", self)
            raise ex


class SaveEsiJobToJsonFile(SaveJobResultToTxtFile):
    """Save an `EsiJob` to file."""

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: str = ".json",
    ) -> None:
        super().__init__(
            job=job,
            mode=mode,
            file_path_template=file_path_template,
            file_ending=file_ending,
        )

    def get_data(self) -> str:
        """ """
        return self.job.serialize_json()


class SaveEsiJobToYamlFile(SaveJobResultToTxtFile):
    """Save an `EsiJob` to file."""

    def __init__(
        self,
        job: EsiJob,
        mode: str = "w",
        file_path_template: Optional[str] = None,
        file_ending: str = ".yaml",
    ) -> None:
        super().__init__(
            job=job,
            mode=mode,
            file_path_template=file_path_template,
            file_ending=file_ending,
        )

    def get_data(self) -> str:
        """ """
        return self.job.serialize_yaml()
