"""Loading and saving data to data dir

Data directory format:
app-data
    static
        schemas
            schema-version
                schema.json
                <generated schema info>
        data
            schema-version
            <static data>
        manifest.json
    dynamic
        schema-version
            history
                <market history data>
        manifest.json
"""
# pylint: disable=empty-docstring, missing-function-docstring
from pathlib import Path
from string import Template
from typing import Dict, Optional

import click

from eve_esi.app_config import APP_DIR, APP_NAME
from eve_esi.pfmsoft.util.collection.misc import optional_object
from eve_esi.pfmsoft.util.file.read_write import load_json, save_json

ROUTE: Dict = {
    "schema": {
        "sub_path": "static/schemas/schema-${version}",
        "file_name": "schema-${version}.json",
    }
}


def get_app_data_directory() -> Path:
    directory = Path(APP_DIR)
    return directory


def get_data_subpath(route_name: str, params: Optional[Dict] = None) -> Path:
    route_template = ROUTE[route_name]["sub_path"]
    params = optional_object(params, dict)
    sub_path = Template(route_template).substitute(params)
    return Path(sub_path)


def get_data_filename(route_name: str, params: Optional[Dict] = None) -> str:
    route_template = ROUTE[route_name]["file_name"]
    params = optional_object(params, dict)
    file_name = Template(route_template).substitute(params)
    return file_name


def save_json_to_app_data(data, route_name: str, params: Optional[Dict] = None):
    app_data_path = get_app_data_directory()
    sub_path = get_data_subpath(route_name, params)
    file_name = get_data_filename(route_name, params)
    file_path = app_data_path / sub_path / Path(file_name)
    save_json(data, file_path, parents=True)
    return file_path


def load_json_from_app_data(data, route_name: str, params: Optional[Dict] = None):
    app_data_path = get_app_data_directory()
    sub_path = get_data_subpath(route_name, params)
    file_name = get_data_filename(route_name, params)
    file_path = app_data_path / sub_path / Path(file_name)
    data = load_json(file_path)
    return data


def clean_app_data():
    """
    [summary]
    clean out app data.
    save configs?

    [extended_summary]
    """
    pass


def app_data_info():
    """
    [summary]
    get info on app data. dates of downloads? schema version?
    make a manifest file in data directory.
    [extended_summary]
    """
    pass
