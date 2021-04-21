import logging
from typing import Any, Callable, Dict, Optional, Sequence, TypeVar, Union

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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


def combine_dictionaries(
    base_dict: dict, additional_dicts: Optional[Sequence[Dict]]
) -> Dict:
    # TODO move this to collection util - NB makes a new dict with
    # optional additional dicts, each overwriting the previous keys
    combined_dict: Dict = {}
    combined_dict.update(base_dict)
    if additional_dicts is not None:
        for override in additional_dicts:
            combined_dict.update(override)
    return combined_dict


def nested_dict(top_dict: Dict, keys: list[str]) -> Optional[Any]:
    """With nested dictionaries, get value from nested dict using a list of keys

    Needs refinement.
    """
    result = top_dict
    for key in keys:
        result = result.get(key, None)
        if result is None:
            return result
    return result
