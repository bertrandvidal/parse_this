import logging
from argparse import Namespace
from typing import Callable, List

from parse_this.args import _get_args_to_parse
from parse_this.exception import ParseThisException
from parse_this.parsing import _get_args_name_from_parser

_LOG = logging.getLogger(__name__)


def _get_parser_call_method(func: Callable):
    """Returns the method that is linked to the 'call' method of the parser

    Args:
        func: the decorated function

    Raises:
        ParseThisException if the decorated method is __init__, __init__ can
        only be decorated in a class decorated by parse_class
    """
    func_name = func.__name__
    parser = func.parser  # type: ignore[attr-defined]

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
        namespace = parser.parse_args(_get_args_to_parse(args))
        if instance is None:
            # If instance is None we are probably decorating a function not a
            # method and don't need the instance
            args_name = _get_args_name_from_parser(parser)
            return _call(func, args_name, namespace)
        return _call_method_from_namespace(instance, func_name, namespace)

    return inner_call


def _call(callable_obj: Callable, arg_names: List[str], namespace: Namespace):
    """Actually calls the callable with the namespace parsed from the command
    line.

    Args:
        callable_obj: a callable object
        arg_names: name of the function arguments
        namespace: the namespace object parsed from the command line
    """
    arguments = {arg_name: getattr(namespace, arg_name) for arg_name in arg_names}
    return callable_obj(**arguments)


def _call_method_from_namespace(obj: Callable, method_name: str, namespace: Namespace):
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
