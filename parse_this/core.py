import argparse
import logging
import sys
from itertools import zip_longest

from parse_this.exception import ParseThisException
from parse_this.help.description import prepare_doc
from parse_this.values import Class, Self, _NO_DEFAULT

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


def _get_arg_parser(func, types, args_and_defaults, delimiter_chars):
    """Return an ArgumentParser for the given function. Arguments are defined
        from the function arguments and their associated defaults.

    Args:
        func: function for which we want an ArgumentParser
        types: types to which the command line arguments should be converted to
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
            arg_type = arg_type or (lambda x: x)
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


def _check_types(func_name, types, func_args, defaults):
    """Make sure that enough types were given to ensure conversion. Also remove
       potential Self/Class arguments.

    Args:
        func_name: name of the decorated function
        types: a list of Python types to which the argument will be converted
        func_args: list of function arguments name
        defaults: tuple of default values for the function argument

    Raises:
        ParseThisException: if the number of types for conversion does not match
            the number of function's arguments
    """
    defaults = defaults or []
    if len(types) > len(func_args):
        raise ParseThisException(
            "To many types provided for conversion for '{}'.".format(func_name)
        )
    if len(types) < len(func_args) - len(defaults):
        raise ParseThisException(
            "Not enough types provided for conversion for '{}'".format(func_name)
        )
    if types and types[0] in [Self, Class]:
        types = types[1:]
        func_args = func_args[1:]
    return types, func_args


def _get_parser_call_method(func):
    """Returns the method that is linked to the 'call' method of the parser

    Args:
        func: the decorated function

    Raises:
        ParseThisException if the decorated method is __init__, __init__ can
        only be decorated in a class decorated by parse_class
    """
    func_name = func.__name__
    parser = func.parser

    def inner_call(instance=None, args=None):
        """This is method attached to <parser>.call.

        Args:
            instance: the instance of the parser
            args: arguments to be parsed
        """
        _LOG.debug("Calling %s.parser.call", func_name)
        # Defer this check in the method call so that __init__ can be
        # decorated in class decorated with parse_class
        if func_name == "__init__":
            raise ParseThisException(
                (
                    "To use 'create_parser' on the"
                    "'__init__' you need to decorate the "
                    "class with '@parse_class'"
                )
            )
        namespace = parser.parse_args(_get_args_to_parse(args, sys.argv))
        if instance is None:
            # If instance is None we are probably decorating a function not a
            # method and don't need the instance
            args_name = _get_args_name_from_parser(parser)
            return _call(func, args_name, namespace)
        return _call_method_from_namespace(instance, func_name, namespace)

    return inner_call


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


def _call(callable_obj, arg_names, namespace):
    """Actually calls the callable with the namespace parsed from the command
    line.

    Args:
        callable_obj: a callable object
        arg_names: name of the function arguments
        namespace: the namespace object parsed from the command line
    """
    arguments = {arg_name: getattr(namespace, arg_name) for arg_name in arg_names}
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
    arg_names = _get_args_name_from_parser(method_parser)
    if method_name == "__init__":
        return _call(obj, arg_names, namespace)
    return _call(method, arg_names, namespace)
