import argparse
import re

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
    defaults = defaults or []
    for (k, v) in zip_longest(args[::-1], defaults[::-1], fillvalue=NoDefault):
        args_and_defaults.append((k, v))
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
        return ("Argument parsing for %s" % func.__name__,
                {arg: "Help message for %s" % arg for arg in args})
    description = []
    args_help = {}
    fill_description = True
    arg_name = None
    for line in func.__doc__.splitlines():
        line = line.strip()
        if line and fill_description:
            description.append(line)
        elif line:
            arg_match = re.match("\b*(?P<arg_name>\w+)\s*%s\s*(?P<help_msg>.+)"
                                 % params_delim, line)
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
    # If an argument is missing a help message we create a simple one
    for argument in args:
        if argument not in args_help:
            args_help[argument] = "Help message for %s" % argument
    return (" ".join(description), args_help)


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
       potential Self/Class arguments.

    Args:
        types: a list of Python types to which the argument should be converted to
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
