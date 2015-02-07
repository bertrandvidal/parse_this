from argparse import ArgumentParser
from functools import wraps
from inspect import getargspec
import re
import sys

try:
    from itertools import izip_longest as zip_longest
except ImportError:
    from itertools import zip_longest


class ParseThisError(Exception):
    """Error base class raised by this module."""


class NoDefault(object):
    """Use to fill the list of args and default to indicate the argument doesn't
        have a default value.
    """


class Self(object):
    """Special value to use as the type of the self parameter of a method."""


class Class(object):
    """Special value to use as the type of the class parameter of a classmethod."""


def _get_args_and_defaults(args, defaults):
    """Return a list of 2-tuples - the argument name and its default value or
        a special value that indicates there is no default value.

    Args:
        args: list of argument name
        defaults: tuple of default values
    """
    args_and_defaults = []
    for (k, v) in zip_longest(args[::-1], defaults[::-1], fillvalue=NoDefault):
        args_and_defaults.append((k, v))
    return args_and_defaults[::-1]


def _prepare_doc(func, args):
    """From the function docstring get the arg parse description and arguments
        help message. If there is no docstring simple description and help
        message are created.

    Args:
        func: the function that needs argument parsing
        args: name of the function arguments
    Returns:
        A tuple containing the description to be used in the argument parser and
        a dict indexed on the callable argument name and their associated help
        message
    """
    if not func.__doc__:
        return ("Argument parsing for %s" % func.__name__,
                {arg: "Help message for %s" % arg for arg in args})
    description = []
    args_help = {}
    fill_description = True
    arg_name = None
    for line in func.__doc__.split("\n"):
        if line.strip() and fill_description:
            description.append(line.strip())
        else:
            # The first empty line marks the end of the method description
            fill_description = False
            arg_match = re.match("\b*(?P<arg_name>\w+):(?P<help_msg>.+)",
                                 line.strip())
            try:
                arg_name = arg_match.groupdict()["arg_name"].strip()
                args_help[arg_name] = arg_match.groupdict()["help_msg"].strip()
            except AttributeError:
                # The line didn't match the pattern we've hit a
                # multiline argument docstring so we add it to the
                # previous argument help message
                if arg_name is not None and line.strip():
                    args_help[arg_name] = " ".join([args_help[arg_name], line.strip()])
    # If an argument is missing a help message we create a simple one
    for argument in args:
        if argument not in args_help:
            args_help[argument] = "Help message for %s" % argument
    return (" ".join(description), args_help)


def _get_arg_parser(func, types, args_and_defaults):
    """Return an ArgumentParser for the given function. Arguments are defined
        from the function arguments and their associated defaults.

    Args:
        func: function for which we want an ArgumentParser
        types: types to which the command line arguments should be converted to
        args_and_defaults: list of 2-tuples (arg_name, arg_default)
    """
    (description, arg_help) = _prepare_doc(
        func, [x for (x, _) in args_and_defaults])
    parser = ArgumentParser(description=description)
    identity_type = lambda x: x
    for ((arg, default), arg_type) in zip_longest(args_and_defaults, types):
        help_msg = arg_help[arg]
        if default is NoDefault:
            arg_type = arg_type or identity_type
            parser.add_argument(arg, help=help_msg, type=arg_type)
        else:
            arg_type = arg_type or type(default)
            parser.add_argument("--%s" % arg, help=help_msg, default=default,
                                type=arg_type)
    return parser


def _get_args_to_parse(args, sys_argv):
    """Return the given arguments if it is not None else sys.argv if it contains
        something, an empty list otherwise.

    Args:
        args: argument to be parsed
        sys_argv: arguments of the command line i.e. sys.argv
    """
    if args is not None:
        return args
    command_line_arguments = sys_argv[1:]
    if command_line_arguments:
        return command_line_arguments
    return []


def _check_types(types, func_args, defaults):
    """Make sure that enough types were given to ensure conversion. Also remove
        a potentiel Self arguments.

    Args:
        types: a list of Python types to which the argument should be converted to
        func_args: list of function arguments name
        defaults: tuple of default values for the function argument
    Raises:
        ParseThisError: if the number of types for conversion does not match
            the number of function's arguments
    """
    if len(types) > len(func_args):
        raise ParseThisError("To many types provided for conversion.")
    if len(types) < len(func_args) - len(defaults):
        raise ParseThisError("Not enough types provided for conversion")
    if types and types[0] in [Self, Class]:
        types = types[1:]
        func_args = func_args[1:]
    return (types, func_args)


def _call(func, func_args, arguments):
    """Actually calls the function with the arguments parsed from the command line.

    Args:
        func: the function to called
        func_args: name of the function arguments
        arguments: the namespace object parse from the command line
    """
    args = []
    for argument in func_args:
        args.append(getattr(arguments, argument))
    return func(*args)


def parse_this(func, types, args=None):
    """Create an ArgumentParser for the given function converting the command line
        arguments according to the list of types.

    Args:
        func: the function for which the command line arguments to be parsed
        types: a list of types - as accepted by argparse - that will be used to
            convert the command line arguments
        args: a list of arguments to be parsed if None sys.argv is used
    """
    (func_args, _, __, defaults) = getargspec(func)
    types, func_args = _check_types(types, func_args, defaults)
    args_and_defaults = _get_args_and_defaults(func_args, defaults)
    parser = _get_arg_parser(func, types, args_and_defaults)
    arguments = parser.parse_args(_get_args_to_parse(args, sys.argv))
    return _call(func, func_args, arguments)


class create_parser(object):
    """Creates an argument parser for the decorated function."""

    def __init__(self, *types):
        """
        Args:
            type: vargs list of types to which the command line arguments should
            be converted to
        """
        self.types = types

    def __call__(self, func):
        """Add an argument parser attribute `parser` to the decorated function.

        Args:
            func: the function for which we want to create an argument parser
        """
        if not hasattr(func, "parser"):
            (func_args, _, _, defaults) = getargspec(func)
            self.types, func_args = _check_types(
                self.types, func_args, defaults)
            args_and_defaults = _get_args_and_defaults(func_args, defaults)
            func.parser = _get_arg_parser(func, self.types, args_and_defaults)

        @wraps(func)
        def decorated(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated

