from functools import wraps
from inspect import getfullargspec
import argparse
import logging
import sys

from parse_this.core import (
    _check_types,
    _get_args_and_defaults,
    _get_arg_parser,
    _get_args_to_parse,
    _call,
    ParseThisError,
    Self,
    Class,
    FullHelpAction,
    _call_method_from_namespace,
    _get_parser_call_method,
    _get_parseable_methods,
)

__all__ = [
    "Self",
    "Class",
    "ParseThisError",
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
    (func_args, _, _, defaults, _, _, _) = getfullargspec(func)
    types, func_args = _check_types(func.__name__, types, func_args, defaults)
    args_and_defaults = _get_args_and_defaults(func_args, defaults)
    parser = _get_arg_parser(func, types, args_and_defaults, delimiter_chars)
    arguments = parser.parse_args(_get_args_to_parse(args, sys.argv))
    return _call(func, func_args, arguments)


class create_parser(object):

    """Creates an argument parser for the decorated function.

    Note:
        The method '__init__' can not be decorated if the class is not
        decorated with 'parse_class'
    """

    def __init__(self, *types, **options):
        """
        Args:
            types: vargs list of types to which the command line arguments
            should be converted to
            options: options to pass to create the parser. Possible values are:
                -delimiter_chars: characters used to separate the parameters
                from their help message in the docstring. Defaults to ':'
                -name: name that will be used for the parser when used in a
                class decorated with `parse_class`. If not provided the name
                of the method will be used
        """
        self._types = types
        self._delimiter_chars = options.get("delimiter_chars", ":")
        self._name = options.get("name", None)

    def __call__(self, func):
        """Add an argument parser attribute `parser` to the decorated function.

        Args:
            func: the function for which we want to create an argument parser
        """
        if not hasattr(func, "parser"):
            _LOG.debug(
                "Creating parser for '%s'%s",
                func.__name__,
                "/%s" % self._name if self._name else "",
            )
            (func_args, _, _, defaults, _, _, _) = getfullargspec(func)
            self._types, func_args = _check_types(
                func.__name__, self._types, func_args, defaults
            )
            args_and_defaults = _get_args_and_defaults(func_args, defaults)
            parser = _get_arg_parser(
                func, self._types, args_and_defaults, self._delimiter_chars
            )
            parser.get_name = lambda: self._name
            func.parser = parser
            func.parser.call = _get_parser_call_method(func)

        @wraps(func)
        def decorated(*args, **kwargs):
            return func(*args, **kwargs)

        return decorated


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
        self._cls = None

    def __call__(self, cls):
        """
        Args:
            cls: class to be decorated
        """
        _LOG.debug("Creating parser for class '%s'", cls.__name__)
        self._cls = cls
        init_parser, methods_to_parse = _get_parseable_methods(cls)
        self._set_class_parser(init_parser, methods_to_parse, cls)
        return cls

    def _add_sub_parsers(self, top_level_parser, methods_to_parse, class_name):
        """Add all the sub-parsers to the top_level_parser.

        Args:
            top_level_parser: the top level parser
            methods_to_parse: dict of method name pointing to their associated
            argument parser
            class_name: name of the decorated class

        Returns:
            a dict of registered name of the parser i.e. sub command name
            pointing to the method real name
        """
        description = "Accessible methods of {}".format(class_name)
        sub_parsers = top_level_parser.add_subparsers(
            description=description, dest="method"
        )
        # Holds the mapping between the name registered for the parser
        # and the method real name. It is useful in the 'inner_call'
        # method retrieve the real method
        parser_to_method = {}
        for method_name, parser in methods_to_parse.items():
            # We use the name provided in 'create_parser` or the name of the
            # decorated method
            parser_name = parser.get_name() or method_name
            # Make the method name compatible for the argument parsing
            if parser_name.startswith("_"):
                if not self._parse_private:
                    # We skip private methods if the caller asked not to
                    # parse them
                    continue
                # 'Private' methods are exposed without their leading or
                # trailing '_'s. Also works for 'special' methods.
                parser_name = parser_name.strip("_")
            parser_name = parser_name.replace("_", "-")
            parser_to_method[parser_name] = method_name
            sub_parsers.add_parser(
                parser_name,
                parents=[parser],
                add_help=False,
                description=parser.description,
            )
        return parser_to_method

    def _set_class_parser(self, init_parser, methods_to_parse, cls):
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
        description = self._description or cls.__doc__
        top_level_parser = argparse.ArgumentParser(
            description=description,
            parents=top_level_parents,
            add_help=False,
            conflict_handler="resolve",
        )
        top_level_parser.add_argument(
            "-h", "--help", action=FullHelpAction, help="Display this help message"
        )
        parser_to_method = self._add_sub_parsers(
            top_level_parser, methods_to_parse, cls.__name__
        )
        # Update the dict with the __init__ method so we can instantiate
        # the decorated class
        if init_parser:
            parser_to_method["__init__"] = "__init__"
        top_level_parser.call = self._get_parser_call_method(parser_to_method)
        cls.parser = top_level_parser

    def _get_parser_call_method(self, parser_to_method):
        """Return the parser special method 'call' that handles sub-command
            calling.

        Args:
            parser_to_method: mapping of the parser registered name
            to the method it is linked to
        """

        def inner_call(args=None, instance=None):
            """Allows to call the method invoked from the command line or
            provided argument.

            Args:
                args: list of arguments to parse, defaults to command line
                arguments
                instance: an instance of the decorated class. If instance is
                None, the default, and __init__ is decorated the object will be
                instantiated on the fly from the command line arguments
            """
            parser = self._cls.parser
            namespace = parser.parse_args(_get_args_to_parse(args, sys.argv))
            if instance is None:
                # If the __init__ method is not part of the method to
                # decorate we cannot instantiate the class
                if "__init__" not in parser_to_method:
                    raise ParseThisError(
                        (
                            "'__init__' method is not decorated. "
                            "Please provide an instance to "
                            "'{}.parser.call' or decorate the "
                            "'__init___' method with "
                            "'create_parser'".format(self._cls.__name__)
                        )
                    )
                # We instantiate the class from the command line arguments
                instance = _call_method_from_namespace(self._cls, "__init__", namespace)
            method_name = parser_to_method[namespace.method]
            return _call_method_from_namespace(instance, method_name, namespace)

        return inner_call
