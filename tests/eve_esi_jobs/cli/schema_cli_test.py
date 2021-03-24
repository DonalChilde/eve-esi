import pytest
from aiohttp import ClientSession
from rich import inspect, print

from eve_esi_jobs.app_data import load_schema
from eve_esi_jobs.cli.schema_cli import download_schema


def test_download_schema():
    schema = download_schema()
    assert schema is not None
    assert schema.get("basePath", None) is not None
