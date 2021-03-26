"""foo"""
import json
from json.encoder import JSONEncoder
from pathlib import Path

import aiofiles

from eve_esi_jobs.app_config import logger
from eve_esi_jobs.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
)

# TODO callback to add results data to EsiJob possibly instead of save to file
# TODO callback to add response data to EsiJob?
# TODO base class save to file, sub for json


class SaveResultToFile(AiohttpActionCallback):
    """Usually used after ResponseToText callback"""

    def __init__(self, file_path: str, mode: str = "w") -> None:
        super().__init__()
        self.file_path = Path(file_path)
        self.mode = mode

    def refine_path(self, caller: AiohttpAction, *args, **kwargs):
        """Refine the file path. Data from the AiohttpAction is available for use here."""
        # noop

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects data to be a string."""
        data = caller.result
        return data

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        self.refine_path(caller, args, kwargs)
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(str(self.file_path), mode=self.mode) as file:
                # with open(self.file_path, mode=self.mode) as file:
                data = self.get_data(caller, args, kwargs)
                await file.write(data)
        except Exception as ex:
            logger.exception("Exception saving file to %s", self.file_path)


class SaveJsonResultToFile(SaveResultToFile):
    """Usually used after ResponseToJson callback."""

    def __init__(self, file_path: str, mode: str = "w") -> None:
        super().__init__(file_path, mode=mode)

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        """expects data (caller.result in super) to be json."""
        data = super().get_data(caller, *args, **kwargs)
        try:
            json_data = json.dumps(data, indent=2)
            return json_data
        except json.JSONDecodeError as ex:
            logger.exception(
                "Unable to decode json data for %s, message was %s", caller, ex
            )
            return json.dumps(
                {
                    "error_msg": "Unable to decode json data for {}, message was {}".format(
                        caller, ex
                    )
                }
            )
