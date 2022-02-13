import logging
import sys
from itertools import zip_longest
from typing import Any, List, Optional, Tuple

_NO_DEFAULT = object()

_LOG = logging.getLogger(__name__)


def _get_args_and_defaults(args: List[str], defaults: Optional[Tuple[Any, ...]] = None):
    """Return a list of 2-tuples - the argument name and its default value or
        a special value that indicates there is no default value.

    Args:
        args: list of argument name
        defaults: tuple of default values
    """
    defaults = defaults or ()
    args_and_defaults = [
        (argument, default)
        for (argument, default) in zip_longest(
            args[::-1], defaults[::-1], fillvalue=_NO_DEFAULT
        )
    ]
    return args_and_defaults[::-1]


def _get_args_to_parse(args: List[str], cli_arguments: Optional[List[str]] = None):
    """Return the given arguments if it is not None else sys.argv if it contains
        something, an empty list otherwise.

    Args:
        args: argument to be parsed
        cli_arguments: arguments from the command line, defaults to sys.argv; mostly
        for testing purposes
    """
    cli_arguments = cli_arguments if cli_arguments is not None else sys.argv
    arguments = args if args is not None else cli_arguments[1:]
    _LOG.debug("Parsing arguments: %s", arguments)
    return arguments
