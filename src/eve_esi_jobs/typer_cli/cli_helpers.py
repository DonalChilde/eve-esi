"""Common helper functions"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

import typer

logger = logging.getLogger(__name__)


def load_json(file_path: Path, **kwargs) -> Any:
    """
    Load a json file.

    :param file_path: :py:class:`pathlib.Path` to the json file.
    :param `**kwargs`: Addtional key word arguments supplied to :func:`json.load()`.
    :raises Exception: Any exception raised during the loading of the file, or the conversion to json.
    :return: The loaded json file.
    """

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file, **kwargs)
        return data
    except Exception as error:
        logger.exception(
            "Error trying to load json file from %s", file_path, exc_info=True
        )
        raise error


def save_json(
    data: Any,
    file_path: Path,
    mode: str = "w",
    indent: int = 2,
    sort_keys: bool = False,
    parents: bool = False,
    exist_ok: bool = True,
    **kwargs,
):
    """
    Save a json file. Can create parent directories if necessary.

    'w' for writing (truncating the file if it already exists), 'x' for exclusive
    creation.

    :param data: Data to save to json file.
    :param file_path: Output :py:class:`pathlib.Path` to json file.
    :param mode: File mode to use. As used in :func:`open`. Limited to 'w' or 'x'. Defaults to 'w'.
    :param indent: Spaces to indent json output. Defaults to 2.
    :param sort_keys: Sort key of json dicts. Defaults to ``False``.
    :param parents: Make parent directories if they don't exist. As used by :func:`pathlib.Path.mkdir()`. Defaults to ``False``.
    :param exist_ok: Suppress exception if parent directory exists as directory. As used by :func:`pathlib.Path.mkdir`. Defaults to ``True``.
    :param `**kwargs`: Addtional key word arguments supplied to :func:`json.dump()`.
    :raises ValueError: If unsupported file mode is used.
    :raises Exception: Any exception raised during the saving of the file, or the conversion from json.
    """

    kwargs["indent"] = indent
    kwargs["sort_keys"] = sort_keys

    try:
        if mode not in ["w", "x"]:
            raise ValueError(f"Unsupported file mode '{mode}'.")
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=parents, exist_ok=exist_ok)
        with open(file_path, mode) as json_file:
            json.dump(data, json_file, **kwargs)
    except Exception as error:
        logger.exception(
            "Error trying to save json data to %s", file_path, exc_info=True
        )
        raise error


def validate_input_path(path_in: str) -> str:
    """
    Ensure the input path exists, raise an error and exit the script if it does not.

    Args:
        path_in: The path as a string

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path.
    """
    input_path: Path = Path(path_in)
    if not input_path.exists():
        raise typer.BadParameter(f"Input path {input_path.resolve()} does not exist.")
    return str(input_path)


def validate_output_path(path_out: str) -> str:
    """
    Checks to see if the path is a file.

    Does not check to see if it is a directory, or if it exists.

    Args:
        path_out: the path as a string.

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path
    """
    output_path: Path = Path(path_out)
    if output_path.is_file():
        raise typer.BadParameter(
            f"Output path {output_path.resolve()} is not a directory."
        )
    return str(output_path)


def load_esi_work_order_json(file_path: Path) -> Dict:
    """
    Load a json file. Exit script on error.

    Args:
        file_path: Path to be loaded.

    Raises:
        typer.BadParameter: [description]
        typer.BadParameter: [description]

    Returns:
        The json file.
    """
    try:
        json_data = load_json(file_path)
    except json.decoder.JSONDecodeError as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()} "
            "are you sure it is a json file?"
        )
    except Exception as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()}\n"
            f"The error reported was {ex.__class__} with msg {ex}"
        )
    return json_data
