import pytest


def test_schema_resource(esi_schema):
    assert esi_schema["info"]["version"] == "1.7.15"


def test_esi_provider(esi_provider):
    assert esi_provider.schema["info"]["version"] == "1.7.15"
