import logging
from inspect import getfullargspec

from parse_this.args import _get_args_and_defaults, _get_args_to_parse
from parse_this.call import (
    _call,
)
from parse_this.exception import ParseThisException
from parse_this.parsers import ClassParser, MethodParser
from parse_this.parsing import (
    _get_arg_parser,
)
from parse_this.types import _check_types
from parse_this.values import Class, Self

__all__ = [
    "Self",
    "Class",
    "ParseThisException",
    "parse_this",
    "create_parser",
    "parse_class",
]


_LOG = logging.getLogger(__name__)


def parse_this(func, types, args=None, delimiter_chars=":"):
    """Create an ArgParser for the given function converting the command line
       arguments according to the list of types.

    Args:
        func: the function for which the command line arguments to be parsed
        types: a list of types - as accepted by argparse - that will be used to
            convert the command line arguments
        args: a list of arguments to be parsed if None sys.argv is used
        delimiter_chars: characters used to separate the parameters from their
        help message in the docstring. Defaults to ':'
    """
    _LOG.debug("Creating parser for %s", func.__name__)
    (func_args, _, _, defaults, _, _, annotations) = getfullargspec(func)
    types, func_args = _check_types(func.__name__, types, func_args, defaults)
    args_and_defaults = _get_args_and_defaults(func_args, defaults)
    parser = _get_arg_parser(
        func, types, annotations, args_and_defaults, delimiter_chars
    )
    arguments = parser.parse_args(_get_args_to_parse(args))
    return _call(func, func_args, arguments)


create_parser = MethodParser

parse_class = ClassParser
