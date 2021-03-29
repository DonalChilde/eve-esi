import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, TypeVar, Union

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


T = TypeVar("T")  # pylint: disable=invalid-name


def optional_object(
    argument: Union[None, T], object_factory: Callable[..., T], *args, **kwargs
) -> T:
    """
    A convenience method for initializing optional arguments.

    Meant to be used when solving the problem of passing an optional object where
    the desired behavior is a new object if None is passed. The problems with this
    are better explained here: https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments

    The standard solution is to use Optional[List] = None, check for None in your code,
    and initialize a new mutable as needed. `optional_object` saves a few line of code.

    For example:

    .. code:: python

        class SomeObject:
            data_1: int
            data_2: str


        class MyClass:
            def __init__(
                self,
                plain_arg: int,
                with_data: Optional[List[str]] = None,
                new_dict: Optional[Dict[str, int]] = None,
                my_class: Optional[SomeObject] = None,
            ):
                default_some_object = {"data_1": 1, "data_2": "two"}
                self.plain_arg = plain_arg
                self.with_data: List[str] = optional_object(with_data, list, ["a", "b", "c"])
                self.new_dict: Dict[str, int] = optional_object(new_dict, dict)
                self.my_class: SomeObject = optional_object(
                    my_class, SomeObject, **default_some_object
                )

    Args:
        argument: An argument that is an object that may be None.
        object_factory: Factory function used to create the object.
        `*args`: Optional arguments passed to factory function.
        `**kwargs`: Optional keyword arguments passed to factory function.

    Returns:
        The initialized object.
    """

    if argument is None:
        return object_factory(*args, **kwargs)
    return argument


def combine_dictionaries(base_dict: dict, overrides: Optional[Sequence[Dict]]) -> Dict:
    # TODO move this to collection util - NB makes a new dict with optional overrides
    combined_dict: Dict = {}
    combined_dict.update(base_dict)
    if overrides is not None:
        for override in overrides:
            combined_dict.update(override)
    return combined_dict
