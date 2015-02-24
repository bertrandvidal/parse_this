from __future__ import print_function
import argparse
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
    """Special value to use as the type of the self arg of a method."""


class Class(object):
    """Special value to use as the type of the cls arg of a classmethod."""


def identity_type(obj):
    """Return the object as is.

    Args:
        obj: the object to be 'cast'

    Note:
        This method is the callable used by the ArgumentParser to parse the
        command line arguments.
    """
    return obj


def _get_args_and_defaults(args, defaults):
    """Return a list of 2-tuples - the argument name and its default value or
        a special value that indicates there is no default value.

    Args:
        args: list of argument name
        defaults: tuple of default values
    """
    defaults = defaults or []
    args_and_defaults = [(argument, default) for (argument, default)
                         in zip_longest(args[::-1], defaults[::-1],
                                        fillvalue=NoDefault)]
    return args_and_defaults[::-1]


def _prepare_doc(func, args, params_delim):
    """From the function docstring get the arg parse description and arguments
        help message. If there is no docstring simple description and help
        message are created.

    Args:
        func: the function that needs argument parsing
        args: name of the function arguments
        params_delim: characters used to separate the parameters from their
        help message in the docstring

    Returns:
        A tuple containing the description to be used in the argument parser and
        a dict indexed on the callable argument name and their associated help
        message
    """
    if not func.__doc__:
        return _get_default_help_message(func, args)
    description = []
    args_help = {}
    fill_description = True
    arg_name = None
    arg_doc_regex = re.compile("\b*(?P<arg_name>\w+)\s*%s\s*(?P<help_msg>.+)" %
                               params_delim)
    for line in func.__doc__.splitlines():
        line = line.strip()
        if line and fill_description:
            description.append(line)
        elif line:
            arg_match = arg_doc_regex.match(line)
            try:
                arg_name = arg_match.groupdict()["arg_name"].strip()
                args_help[arg_name] = arg_match.groupdict()["help_msg"].strip()
            except AttributeError:
                # The line didn't match the pattern we've hit a
                # multiline argument docstring so we add it to the
                # previous argument help message
                if arg_name is not None:
                    args_help[arg_name] = " ".join([args_help[arg_name], line])
        else:
            # The first empty line we encountered means we are done with
            # the description. The first empty line we encounter after
            # filling the argument help means we are done with argument
            # parsing.
            if not fill_description and args_help:
                break
            fill_description = False
    return _get_default_help_message(func, args, " ".join(description),
                                     args_help)


def _get_parseable_methods(cls):
    """Return all methods of cls that are parseable i.e. have been decorated
    by '@create_parser'.

    Args:
        cls: the class currently being decorated

    Returns:
        a 2-tuple with the parser of the __init__ method if any and a dict
        of the form {'method_name': associated_parser}
    """
    init_parser = None
    methods_to_parse = {}
    for name, obj in vars(cls).items():
        # Every callable object that has a 'parser' attribute will be
        # added as a subparser.
        # This won't work for classmethods because reference to
        # classmethods are only possible once the class has been defined
        if callable(obj) and hasattr(obj, "parser"):
            if name == "__init__":
                # If we find the decorated __init__ method it will be
                # used as the top level parser
                init_parser = obj.parser
            else:
                methods_to_parse[obj.__name__] = obj.parser
    return (init_parser, methods_to_parse)


def _get_default_help_message(func, args, description=None, args_help=None):
    """Create a default description for the parser and help message for the
    agurments if they are missing.

    Args:
        func: the method we are creating a parser for
        args: the argument names of the method
        description: a potentially existing description created from the
        function docstring
        args_help: a dict {arg_name: help} with potentially missing arguments
    """
    if description is None:
        description = "Argument parsing for %s" % func.__name__
    args_help = args_help or {}
    # If an argument is missing a help message we create a simple one
    for argument in [arg_name for arg_name in args
                     if arg_name not in args_help]:
        args_help[argument] = "Help message for %s" % argument
    return (description, args_help)


def _get_arg_parser(func, types, args_and_defaults, params_delim):
    """Return an ArgumentParser for the given function. Arguments are defined
        from the function arguments and their associated defaults.

    Args:
        func: function for which we want an ArgumentParser
        types: types to which the command line arguments should be converted to
        args_and_defaults: list of 2-tuples (arg_name, arg_default)
        params_delim: characters used to separate the parameters from their
        help message in the docstring
    """
    (description, arg_help) = _prepare_doc(
        func, [x for (x, _) in args_and_defaults], params_delim)
    parser = argparse.ArgumentParser(description=description)
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
    return args if args is not None else sys_argv[1:]


def _check_types(types, func_args, defaults):
    """Make sure that enough types were given to ensure conversion. Also remove
       potential Self/Class arguments.

    Args:
        types: a list of Python types to which the argument will be converted
        func_args: list of function arguments name
        defaults: tuple of default values for the function argument

    Raises:
        ParseThisError: if the number of types for conversion does not match
            the number of function's arguments
    """
    defaults = defaults or []
    if len(types) > len(func_args):
        raise ParseThisError("To many types provided for conversion.")
    if len(types) < len(func_args) - len(defaults):
        raise ParseThisError("Not enough types provided for conversion")
    if types and types[0] in [Self, Class]:
        types = types[1:]
        func_args = func_args[1:]
    return (types, func_args)


def _get_parser_call_method(parser, method_name):
    """Returns the method that is linked to the 'call' method of the parser

    Args:
        parser: The parser that will used to parse the command line args
        method_name: name of the decorated method

    Raises:
        ParseThisError if the decorated method is __init__, __init__ can
        only be decorated in a class decorated by parse_class
    """

    def inner_call(instance, args=None):
        """This is method attached to <parser>.call.

        Args:
            instance: the instance of the parser
            args: arguments to be parsed
        """
        # Defer this check in the method call so that __init__ can be
        # decorated in class decorated with parse_class
        if method_name == "__init__":
            raise ParseThisError(("To use 'create_parser' on the"
                                  "'__init__' you need to decorate the "
                                  "class with '@parse_class'"))
        namespace = parser.parse_args(args or sys.argv[1:])
        return _call_method_from_namespace(instance, method_name, namespace)

    return inner_call


def _call(callable_obj, arg_names, namespace):
    """Actually calls the callable with the namespace parsed from the command
    line.

    Args:
        callable_obj: a callable object
        arg_names: name of the function arguments
        namespace: the namespace object parsed from the command line
    """
    arguments = {arg_name: getattr(namespace, arg_name)
                 for arg_name in arg_names}
    return callable_obj(**arguments)


def _call_method_from_namespace(obj, method_name, namespace):
    """Call the method, retrieved from obj, with the correct arguments via
    the namespace

    Args:
        obj: any kind of object
        method_name: method to be called
        namespace: an argparse.Namespace object containing parsed command
        line arguments
    """
    method = getattr(obj, method_name)
    method_parser = method.parser
    # Retrieve the 'action' destination of the method parser i.e. its
    # argument name. The HelpAction is ignored.
    arg_names = [action.dest for action in method_parser._actions if not
                 isinstance(action, argparse._HelpAction)]
    if method_name == "__init__":
        return _call(obj, arg_names, namespace)
    return _call(method, arg_names, namespace)


class FullHelpAction(argparse._HelpAction):
    """Custom HelpAction to display help from all subparsers.

    This allows to have the help for all sub-commands when invoking:
    '<script.py> --help' rather than a somewhat incomplete help message only
    describing the name of the sub-commands.
    Note: taken from http://stackoverflow.com/a/24122778/2003420
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # Print help for the parser this class is linked to
        parser.print_help()
        # Retrieve sub-parsers of the given parser
        subparsers_actions = [action for action in parser._actions
                              if isinstance(action, argparse._SubParsersAction)]
        for subparser_action in subparsers_actions:
            # Get all subparsers and print their help
            for choice, subparser in subparser_action.choices.items():
                print("** Command '{}' **".format(choice))
                print("{}\n".format(subparser.format_help()))
        parser.exit()
