import logging
from itertools import zip_longest

from parse_this.values import _NO_DEFAULT

_LOG = logging.getLogger(__name__)


def _get_args_and_defaults(args, defaults):
    """Return a list of 2-tuples - the argument name and its default value or
        a special value that indicates there is no default value.

    Args:
        args: list of argument name
        defaults: tuple of default values
    """
    defaults = defaults or []
    args_and_defaults = [
        (argument, default)
        for (argument, default) in zip_longest(
            args[::-1], defaults[::-1], fillvalue=_NO_DEFAULT
        )
    ]
    return args_and_defaults[::-1]


def _get_args_to_parse(args, sys_argv):
    """Return the given arguments if it is not None else sys.argv if it contains
        something, an empty list otherwise.

    Args:
        args: argument to be parsed
        sys_argv: arguments of the command line i.e. sys.argv
    """
    arguments = args if args is not None else sys_argv[1:]
    _LOG.debug("Parsing arguments: %s", arguments)
    return arguments
