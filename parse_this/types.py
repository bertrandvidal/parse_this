from typing import Callable, Dict, List, Tuple

from parse_this.exception import ParseThisException


def _check_types(
    func_name: str,
    annotations: Dict[str, Callable],
    func_args: List[str],
    defaults: Tuple,
):
    """Make sure that enough types were given to ensure conversion. Also remove
       potential 'self'/'cls' from the function arguments.

    Args:
        func_name: name of the decorated function
        annotations: annotations extract from a function signature
        func_args: list of function arguments name
        defaults: tuple of default values for the function argument

    Raises:
        ParseThisException: we cannot infer the type of all of the arguments using
        the annotations and the default values
    """
    defaults = defaults or ()
    types_annotations = dict(annotations)

    if "return" in types_annotations:
        del types_annotations["return"]

    if func_args and func_args[0] in ("self", "cls"):
        func_args = func_args[1:]

    if len(types_annotations) > len(func_args):
        raise ParseThisException(
            "Too many types provided for conversion for '{}'.".format(func_name)
        )
    if len(types_annotations) < len(func_args) - len(defaults):
        raise ParseThisException(
            "Not enough types provided for conversion for '{}'".format(func_name)
        )
    return func_args
