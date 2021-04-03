import pytest
from tests.eve_esi_jobs.conftest import FileResource


def test_schema_resource(esi_schema: FileResource):
    assert esi_schema.data["info"]["version"] == "1.7.15"


def test_esi_provider(esi_provider):
    assert esi_provider.schema["info"]["version"] == "1.7.15"
