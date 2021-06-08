import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from rich import inspect

from eve_esi_jobs import models


def test_foo(logger: logging.Logger):
    assert True


def test_get_iso_time():
    print(datetime.now().isoformat().replace(":", "-"))
