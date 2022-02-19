import logging
import typing
from argparse import ArgumentParser
from functools import wraps
from inspect import getfullargspec
from typing import Callable, Dict, Optional, Type

from parse_this.args import _get_args_and_defaults, _get_args_to_parse
from parse_this.call import _call, _call_method_from_namespace, _get_parser_call_method
from parse_this.exception import ParseThisException
from parse_this.help.action import FullHelpAction
from parse_this.parsing import _get_arg_parser, _get_parseable_methods
from parse_this.types import _check_types

_LOG = logging.getLogger(__name__)


class FunctionParser(object):
    """Parse command line arguments, transform them to the appropriate type and
    delegate the call to a given callable.
    """

    def __call__(
        self, func: Callable, args: typing.List[str] = None, delimiter_chars: str = ":"
    ):
        """Create an ArgParser for the given function converting the command line
           arguments and passing them to the function, return the result of the
           function call.

        Args:
            func: the function for which the command line arguments to be parsed
            args: a list of arguments to be parsed if None sys.argv is used
            delimiter_chars: characters used to separate the parameters from their
            help message in the docstring. Defaults to ':'
        """
        _LOG.debug("Creating parser for %s", func.__name__)
        (func_args, _, _, defaults, _, _, annotations) = getfullargspec(func)
        func_args = _check_types(func.__name__, annotations, func_args, defaults)
        args_and_defaults = _get_args_and_defaults(func_args, defaults)
        parser = _get_arg_parser(func, annotations, args_and_defaults, delimiter_chars)
        self._set_function_parser(func, parser)
        arguments = parser.parse_args(_get_args_to_parse(args))
        return _call(func, func_args, arguments)

    @typing.no_type_check
    def _set_function_parser(self, func: Callable, parser: ArgumentParser):
        func.parser = parser


class MethodParser(object):
    """Creates an argument parser for the decorated function.

    Note:
        The method '__init__' can not be decorated if the class is not
        decorated with 'parse_class'
    """

    _name: Optional[str]
    _delimiter_chars: str

    def __init__(self, delimiter_chars: str = ":", name: str = None):
        """
        Args:
            delimiter_chars: characters used to separate the parameters from their
            help message in the docstring.
            name: name that will be used for the parser when used in a class
            decorated with `parse_class`. If not provided the name of the method will
            be used
        """
        self._delimiter_chars = delimiter_chars
        self._name = name

    def __call__(self, func: Callable):
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
            (func_args, _, _, defaults, _, _, annotations) = getfullargspec(func)
            func_args = _check_types(func.__name__, annotations, func_args, defaults)
            args_and_defaults = _get_args_and_defaults(func_args, defaults)
            parser = _get_arg_parser(
                func, annotations, args_and_defaults, self._delimiter_chars
            )
            parser.get_name = lambda: self._name or func.__name__
            self._set_method_parser(func, parser)

        @wraps(func)
        def decorated(*args, **kwargs):
            return func(*args, **kwargs)

        return decorated

    @typing.no_type_check
    def _set_method_parser(self, func: Callable, parser: ArgumentParser):
        func.parser = parser
        func.parser.call = _get_parser_call_method(func)


class ClassParser(object):
    """Allows to create a global argument parser for a class along with
    subparsers with each if its properly decorated methods."""

    _parse_private: bool
    _description: Optional[str]
    _cls: Type = None

    def __init__(self, description: str = None, parse_private: bool = False):
        """

        Args:
            description: give a specific description for the top level parser,
            if not specified it will be the class docstring.
            parse_private: specifies whether or not 'private' methods should be
            parsed, defaults to False
        """
        self._description = description
        self._parse_private = parse_private

    def __call__(self, cls: Type):
        """
        Args:
            cls: class to be decorated
        """
        _LOG.debug("Creating parser for class '%s'", cls.__name__)
        self._cls = cls
        init_parser, methods_to_parse = _get_parseable_methods(cls)
        self._set_class_parser(init_parser, methods_to_parse, cls)
        return cls

    def _add_sub_parsers(
        self,
        top_level_parser,
        methods_to_parse: Dict[str, ArgumentParser],
        class_name: str,
    ):
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
            parser_name = parser.get_name()  # type: ignore[attr-defined]
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

    def _set_class_parser(
        self,
        init_parser: ArgumentParser,
        methods_to_parse: Dict[str, ArgumentParser],
        cls: Type,
    ):
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
        top_level_parser = ArgumentParser(
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
        self._set_parser_call_method(parser_to_method, top_level_parser)
        cls.parser = top_level_parser

    @typing.no_type_check
    def _set_parser_call_method(
        self, parser_to_method: Dict[str, str], top_level_parser: ArgumentParser
    ):
        top_level_parser.call = self._get_parser_call_method(parser_to_method)

    def _get_parser_call_method(self, parser_to_method: Dict[str, Callable]):
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
                args: list of arguments to parse, defaults to command line arguments
                instance: an instance of the decorated class. If instance is None,
                    the default, and __init__ is decorated the object will be
                    instantiated on the fly from the command line arguments
            """
            parser = self._cls.parser
            namespace = parser.parse_args(_get_args_to_parse(args))
            if instance is None:
                # If the __init__ method is not part of the method to
                # decorate we cannot instantiate the class
                if "__init__" not in parser_to_method:
                    raise ParseThisException(
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
