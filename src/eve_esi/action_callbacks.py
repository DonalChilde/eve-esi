"""foo"""
import json
from pathlib import Path

import aiofiles
from rich import print

from eve_esi.app_config import logger
from eve_esi.pfmsoft.util.async_actions.aiohttp import (
    AiohttpAction,
    AiohttpActionCallback,
)


class SaveResultToFile(AiohttpActionCallback):
    def __init__(self, file_path: str, mode: str = "w") -> None:
        super().__init__()
        self.file_path = Path(file_path)
        self.mode = mode

    def refine_path(self, caller: AiohttpAction, *args, **kwargs):
        pass

    def get_data(self, caller: AiohttpAction, *args, **kwargs) -> str:
        data = json.dumps(caller.result, indent=2)
        return data

    async def do_callback(self, caller: AiohttpAction, *args, **kwargs):
        self.refine_path(caller, args, kwargs)
        try:
            self.file_path.parent.mkdir(parents=True)
            async with aiofiles.open(str(self.file_path), mode=self.mode) as file:
                # with open(self.file_path, mode=self.mode) as file:
                data = self.get_data(caller, args, kwargs)
                await file.write(data)
        except Exception as ex:
            logger.exception("Exception saving file to %s", self.file_path)
