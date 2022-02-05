import argparse
import logging
from itertools import zip_longest

from parse_this.exception import ParseThisException
from parse_this.help.description import prepare_doc
from parse_this.values import _NO_DEFAULT

_LOG = logging.getLogger(__name__)


def _get_parseable_methods(cls):
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


def _get_arg_parser(func, types, annotations, args_and_defaults, delimiter_chars):
    """Return an ArgumentParser for the given function. Arguments are defined
        from the function arguments and their associated defaults.

    Args:
        func: function for which we want an ArgumentParser
        types: types to which the command line arguments should be converted to
        annotations: is a dictionary mapping parameter names to annotations,
        takes precedence over types
        args_and_defaults: list of 2-tuples (arg_name, arg_default)
        delimiter_chars: characters used to separate the parameters from their
        help message in the docstring
    """
    _LOG.debug("Creating ArgumentParser for '%s'", func.__name__)
    (description, arg_help) = prepare_doc(
        func, [x for (x, _) in args_and_defaults], delimiter_chars
    )
    parser = argparse.ArgumentParser(description=description)
    for ((arg, default), arg_type) in zip_longest(args_and_defaults, types):
        help_msg = arg_help[arg]
        if default is _NO_DEFAULT:
            arg_type = annotations.get(arg) or arg_type or (lambda x: x)
            if arg_type == bool:
                _LOG.debug("Adding optional flag %s.%s", func.__name__, arg)
                parser.add_argument(
                    "--%s" % arg,
                    default=True,
                    required=False,
                    action="store_false",
                    help="%s. Defaults to True if not specified" % help_msg,
                )
            else:
                _LOG.debug("Adding positional argument %s.%s", func.__name__, arg)
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
                _LOG.debug("Adding optional flag %s.%s", func.__name__, arg)
                parser.add_argument(
                    "--%s" % arg, help=help_msg, default=default, action=action
                )
            else:
                _LOG.debug("Adding optional argument %s.%s", func.__name__, arg)
                parser.add_argument(
                    "--%s" % arg, help=help_msg, default=default, type=arg_type
                )
    return parser


def _get_args_name_from_parser(parser):
    """Retrieve the name of the function argument linked to the given parser.

    Args:
        parser: a function parser
    """
    # Retrieve the 'action' destination of the method parser i.e. its
    # argument name. The HelpAction is ignored.
    return [
        action.dest
        for action in parser._actions
        if not isinstance(action, argparse._HelpAction)
    ]
