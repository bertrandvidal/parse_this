import logging
from argparse import Namespace
from functools import wraps
from typing import Any, Callable, List, Optional

from parse_this.args import _get_args_to_parse
from parse_this.exception import ParseThisException
from parse_this.helpers import _get_args_name_from_parser

_LOG = logging.getLogger(__name__)


def _get_parser_call_method(func: Callable) -> Callable:
    """Returns the method that is linked to the 'call' method of the parser

    Args:
        func: the decorated function

    Raises:
        ParseThisException if the decorated method is __init__, __init__ can
        only be decorated in a class decorated by parse_class
    """
    func_name = func.__name__
    parser = func.parser  # type: ignore[attr-defined]

    @wraps(func)
    def inner_call(instance: Any = None, args: Optional[List[str]] = None) -> Any:
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
            varargs_name = getattr(parser, "_parse_this_varargs", None)
            return _call(func, args_name, namespace, varargs_name=varargs_name)
        return _call_method_from_namespace(instance, func_name, namespace)

    return inner_call


def _call(
    callable_obj: Callable,
    arg_names: List[str],
    namespace: Namespace,
    varargs_name: Optional[str] = None,
) -> Any:
    """Actually calls the callable with the namespace parsed from the command
    line.

    Args:
        callable_obj: a callable object
        arg_names: name of the function arguments
        namespace: the namespace object parsed from the command line
        varargs_name: optional name of the *args parameter; when provided,
        the matching entry in the arguments dict is splatted as positional
        arguments instead of being passed as a keyword.
    """
    try:
        logging.basicConfig(level=namespace.log_level)
    except AttributeError:
        pass
    arguments = {arg_name: getattr(namespace, arg_name) for arg_name in arg_names}
    if varargs_name is not None:
        # When the signature has *args, the regular positional-or-keyword
        # params before it must be passed positionally — mixing them with a
        # splatted varargs tuple via **kwargs collides on parameter 0. arg_names
        # is in parser-action add order, which matches signature order, so
        # collecting non-varargs values in that order reproduces the call.
        varargs_values = arguments.pop(varargs_name, [])
        positional = [arguments[name] for name in arg_names if name != varargs_name]
        return callable_obj(*positional, *varargs_values)
    return callable_obj(**arguments)


def _call_method_from_namespace(
    obj: Any, method_name: str, namespace: Namespace
) -> Any:
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
    varargs_name = getattr(method_parser, "_parse_this_varargs", None)
    if method_name == "__init__":
        return _call(obj, arg_names, namespace, varargs_name=varargs_name)
    return _call(method, arg_names, namespace, varargs_name=varargs_name)
