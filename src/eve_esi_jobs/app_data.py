"""Loading and saving data in the app data dir.

manifest.json will support metadata for each file. Maybe include support for ETag,
or somekind of caching expiration.

| Data directory format:
| app-data
|     static
|         schemas
|             schema-version
|                 schema.json
|                 <generated schema info>
|         data
|             schema-version
|             <static data>
|         manifest.json
|     dynamic
|         schema-version
|             history
|                 <market history data>
|         manifest.json

"""

# pylint: disable=empty-docstring, missing-function-docstring

from pathlib import Path
from string import Template
from typing import Dict, List, Optional

from eve_esi_jobs.app_config import APP_DIR, logger
from eve_esi_jobs.helpers import load_json, optional_object, save_json

ROUTE: Dict = {
    "schema": {
        "sub_path": "static/schemas",
        "version": "schema-${version}",
        "file_name": "schema-${version}.json",
    }
}
"""Routes to file locations by key"""


def get_app_data_directory() -> Path:
    """Get the app data directory."""
    directory = Path(APP_DIR)
    return directory


def get_data_subpath(route_name: str, params: Optional[Dict] = None) -> Path:
    sub_path_template = ROUTE[route_name]["sub_path"]
    params = optional_object(params, dict)
    sub_path = Template(sub_path_template).substitute(params)
    return Path(sub_path)


def get_data_version(route_name: str, params: Optional[Dict] = None) -> Path:
    version_template = ROUTE[route_name]["version"]
    params = optional_object(params, dict)
    version = Template(version_template).substitute(params)
    return Path(version)


def get_data_filename(route_name: str, params: Optional[Dict] = None) -> str:
    route_template = ROUTE[route_name]["file_name"]
    params = optional_object(params, dict)
    file_name = Template(route_template).substitute(params)
    return file_name


def save_json_to_app_data(
    data, route_name: str, params: Optional[Dict] = None
) -> Optional[Path]:
    app_data_path = get_app_data_directory()
    sub_path = get_data_subpath(route_name, params)
    version = get_data_version(route_name, params)
    file_name = get_data_filename(route_name, params)
    file_path = app_data_path / sub_path / version / Path(file_name)
    try:
        save_json(data, file_path, parents=True)
    except Exception as ex:
        logger.error(
            "Unable to save %s with params: %s to path %s Error message: %s",
            route_name,
            params,
            file_path,
            ex,
        )
        return None
    return file_path


def load_json_from_app_data(
    route_name: str, params: Optional[Dict] = None
) -> Optional[Dict]:
    app_data_path = get_app_data_directory()
    sub_path = get_data_subpath(route_name, params)
    version = get_data_version(route_name, params)
    file_name = get_data_filename(route_name, params)
    file_path = app_data_path / sub_path / version / Path(file_name)
    try:
        data = load_json(file_path)
    except Exception as ex:
        logger.error(
            "Unable to load %s with params: %s to path %s\nError message: %s",
            route_name,
            params,
            file_path,
            ex,
        )
        raise ex
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


def get_directory_versions(parent: Path) -> List[str]:
    """
    [summary]
    get list of directories
    strip out versions
    make a list
    [extended_summary]

    :param parent: [description]
    :type parent: Path
    :return: [description]
    :rtype: List[str]
    """
    # FIXME
    return ["1.7.15"]


def most_recent_version(versions: List[str]) -> str:
    # FIXME make smarter about 7 vs 10
    versions.sort()
    return versions[0]


def load_schema(version: str) -> Optional[Dict]:
    if version == "latest":
        schema_parent = get_data_subpath("schema")
        versions = get_directory_versions(schema_parent)
        version = most_recent_version(versions)
    schema = load_json_from_app_data("schema", {"version": version})
    return schema
