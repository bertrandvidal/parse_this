import logging
from argparse import ArgumentParser, _HelpAction
from typing import Any, Callable, Dict, List, Tuple, Type

from parse_this.args import _NO_DEFAULT
from parse_this.exception import ParseThisException
from parse_this.help.description import prepare_doc

_LOG = logging.getLogger(__name__)


def _get_parseable_methods(cls: Type):
    """Return all methods of cls that are parseable i.e. have been decorated
    by '@create_parser'.

    Args:
        cls: the class currently being decorated

    Note:
        classmethods will not be included as they can only be referenced once
        the class has been defined
    Returns:
        a 2-tuple with the parser of the __init__ method if any and a dict
        of the form {'method_name': associated_parser}
    """
    _LOG.debug("Retrieving parseable methods for '%s'", cls.__name__)
    init_parser = None
    methods_to_parse = {}
    for name, obj in vars(cls).items():
        # Every callable object that has a 'parser' attribute will be
        # added as a subparser.
        # This won't work for classmethods because reference to
        # classmethods are only possible once the class has been defined
        if callable(obj) and hasattr(obj, "parser"):
            _LOG.debug("Found method '%s'", name)
            if name == "__init__":
                # If we find the decorated __init__ method it will be
                # used as the top level parser
                init_parser = obj.parser
            else:
                methods_to_parse[obj.__name__] = obj.parser
    return init_parser, methods_to_parse


def _add_log_level_argument(parser: ArgumentParser):
    parser.add_argument(
        "--log-level", required=False, choices=list(logging._nameToLevel.keys())
    )


def _get_arg_parser(
    func: Callable,
    annotations: Dict[str, Callable],
    args_and_defaults: List[Tuple[str, Any]],
    delimiter_chars: str,
    log_level: bool = False,
):
    """Return an ArgumentParser for the given function. Arguments are defined
        from the function arguments and their associated defaults.

    Args:
        func: function for which we want an ArgumentParser
        annotations: is a dictionary mapping parameter names to annotations
        args_and_defaults: list of 2-tuples (arg_name, arg_default)
        delimiter_chars: characters used to separate the parameters from their
        help message in the docstring
        log_level: indicate whether or not a '--log-level' argument should be
        handled to set the log level during the execution
    """
    _LOG.debug("Creating ArgumentParser for '%s'", func.__name__)
    (description, arg_help) = prepare_doc(
        func, [x for (x, _) in args_and_defaults], delimiter_chars
    )
    parser = ArgumentParser(description=description)
    if log_level:
        _add_log_level_argument(parser)
    for (arg, default) in args_and_defaults:
        help_msg = arg_help[arg]
        arg_type = annotations.get(arg)
        if default is _NO_DEFAULT:
            arg_type = arg_type or (lambda x: x)
            if arg_type == bool:
                _LOG.debug(
                    "Adding optional flag %s.%s (default: True)", func.__name__, arg
                )
                parser.add_argument(
                    "--%s" % arg,
                    default=True,
                    required=False,
                    action="store_false",
                    help="%s. Defaults to True if not specified" % help_msg,
                )
            else:
                _LOG.debug(
                    "Adding positional argument %s.%s: %s", func.__name__, arg, arg_type
                )
                parser.add_argument(arg, help=help_msg, type=arg_type)
        else:
            if default is None and arg_type is None:
                raise ParseThisException(
                    "To use default value of 'None' you need "
                    "to specify the type of the argument '{}' "
                    "for the method '{}'".format(arg, func.__name__)
                )
            arg_type = arg_type or type(default)
            if arg_type == bool:
                action = "store_false" if default else "store_true"
                _LOG.debug(
                    "Adding optional flag %s.%s (default: %s)",
                    func.__name__,
                    arg,
                    default,
                )
                parser.add_argument(
                    "--%s" % arg, help=help_msg, default=default, action=action
                )
            else:
                _LOG.debug(
                    "Adding optional argument %s.%s: %s (default: %s)",
                    func.__name__,
                    arg,
                    arg_type,
                    default,
                )
                parser.add_argument(
                    "--%s" % arg, help=help_msg, default=default, type=arg_type
                )
    return parser


def _get_args_name_from_parser(parser: ArgumentParser):
    """Retrieve the name of the function argument linked to the given parser.

    Args:
        parser: a function parser
    """
    # Retrieve the 'action' destination of the method parser i.e. its
    # argument name. The HelpAction is ignored.
    return [
        action.dest for action in parser._actions if not isinstance(action, _HelpAction)
    ]
