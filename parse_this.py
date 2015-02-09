import argparse
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
        a potentiel Self arguments.

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


def parse_this(func, types, args=None, params_delim=":"):
    """Create an ArgumentParser for the given function converting the command line
        arguments according to the list of types.

    Args:
        func: the function for which the command line arguments to be parsed
        types: a list of types - as accepted by argparse - that will be used to
            convert the command line arguments
        args: a list of arguments to be parsed if None sys.argv is used
        params_delim: characters used to separate the parameters from their
        help message in the docstring. Defaults to ':'
    """
    (func_args, _, __, defaults) = getargspec(func)
    types, func_args = _check_types(types, func_args, defaults)
    args_and_defaults = _get_args_and_defaults(func_args, defaults)
    parser = _get_arg_parser(func, types, args_and_defaults, params_delim)
    arguments = parser.parse_args(_get_args_to_parse(args, sys.argv))
    return _call(func, func_args, arguments)


class create_parser(object):
    """Creates an argument parser for the decorated function."""

    def __init__(self, *types, **options):
        """
        Args:
            types: vargs list of types to which the command line arguments should
            be converted to
            options: options to pass to create the parser. Possible values are:
            params_delim: characters used to separate the parameters from their
            help message in the docstring. Defaults to ':'
        """
        self.types = types
        self.params_delim = options.get("params_delim",":")

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
            func.parser = _get_arg_parser(func, self.types, args_and_defaults,
                                          self.params_delim)

        @wraps(func)
        def decorated(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated


class _HelpAction(argparse._HelpAction):
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


class parse_class(object):
    """Allows to create a global argument parser for a class along with
    subparsers with each if its properly decorated methods."""

    def __init__(self, description=None, parse_private=False):
        """

        Args:
            description: give a specific description for the top level parser,
            if not specified it will be the class docstring.
            parse_private: specifies whether or not 'private' methods should be
            parsed, defaults to False
        """
        self._description = description
        self._parse_private = parse_private

    def __call__(self, cls):
        """
        Args:
            cls: class to get decorated
        """
        init_parser, methods_to_parse = self._get_parseable_methods(cls)
        return self._get_class_parser(init_parser, methods_to_parse, cls)

    def _get_parseable_methods(self, cls):
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

    def _get_class_parser(self, init_parser, methods_to_parse, cls):
        """Creates the complete argument parser for the decorated class.

        Args:
            init_parser: argument parser for the __init__ method or None
            methods_to_parse: dict of method name pointing to their associated
            argument parser
            cls: the class we are decorating

        Returns:
            The decorated class with an added attribute 'parser'
        """
        top_level_parents = [init_parser] if init_parser else []
        top_level_parser = argparse.ArgumentParser(description=self._description or cls.__doc__,
                                                   parents=top_level_parents,
                                                   add_help=False,
                                                   conflict_handler="resolve")
        top_level_parser.add_argument("-h", "--help", action=_HelpAction,
                                      help="Display this help message")
        description = "Accessible methods of {}".format(cls.__name__)
        sub_parsers = top_level_parser.add_subparsers(description=description,
                                                      dest="method")
        for method_name, parser in methods_to_parse.items():
            # Make the method name compatible for the argument parsing
            if method_name.startswith("_"):
                if not self._parse_private:
                    # We skip private methods if the caller asked not to
                    # parse them
                    continue
                # 'Private' methods are exposed without their leading '_'
                method_name = method_name[1:]
            parser_name = method_name.replace("_", "-")
            sub_parsers.add_parser(parser_name, parents=[parser],
                                   add_help=False,
                                   description=parser.description)
        cls.parser = top_level_parser
        return cls
