import enum
import inspect
import logging
import types
import typing
from argparse import ArgumentParser, ArgumentTypeError, _HelpAction
from typing import Any, Callable, Literal, Tuple, Type, get_args, get_origin

from parse_this.exception import ParseThisException

_LOG = logging.getLogger(__name__)

# typing.Optional[T] and Union[T, None] both resolve to typing.Union.
# PEP 604 'T | None' resolves to types.UnionType (different origin).
_UNION_ORIGINS: Tuple[Any, ...] = (typing.Union, types.UnionType)


def _unwrap_optional(arg_type: Any) -> Any:
    """Unwrap Optional[T] / Union[T, None] / PEP 604 'T | None' to T.

    Args:
        arg_type: the type annotation to inspect

    Returns:
        the single non-None arm of a Union annotation when exactly one arm is
        non-None; the original arg_type otherwise.

    Raises:
        ParseThisException: if arg_type is a Union with more than one non-None
        arm (e.g. Union[int, str]) — parse_this cannot pick a single converter.
    """
    origin = get_origin(arg_type)
    if origin not in _UNION_ORIGINS:
        return arg_type
    non_none = tuple(a for a in get_args(arg_type) if a is not type(None))
    if len(non_none) > 1:
        raise ParseThisException(
            f"Union type {arg_type!r} with multiple non-None arms is not "
            f"supported: parse_this cannot pick which converter to use. "
            f"Use a single concrete type or Optional[T] (i.e. Union[T, None])."
        )
    # Python collapses Union[None] and Union[T] so a reachable Union with
    # an all-None arms list is impossible — non_none always has exactly one
    # element when we get here.
    return non_none[0]


def _is_enum_type(arg_type: Any) -> bool:
    """Return True if arg_type is a concrete subclass of enum.Enum.

    Args:
        arg_type: the type annotation to inspect

    Note:
        The base class enum.Enum itself is excluded because it has no members,
        so registering it as a choices argument would produce an argument that
        can never be satisfied.
    """
    return (
        inspect.isclass(arg_type)
        and arg_type is not enum.Enum
        and issubclass(arg_type, enum.Enum)
    )


def _make_enum_converter(
    enum_class: Type[enum.Enum],
) -> Callable[[str], enum.Enum]:
    """Return a callable that converts a string name to an enum member.

    Args:
        enum_class: the Enum class whose members are valid choices

    Returns:
        a callable that accepts a string name and returns the matching
        enum member

    Note:
        The converter raises ArgumentTypeError, not ValueError, on unknown
        names. argparse silently discards the ValueError message and falls
        back to a generic "invalid <type> value" using the converter's
        __name__, e.g.:
            error: argument color: invalid _convert value: 'PURPLE'
        ArgumentTypeError preserves the message verbatim, giving users the
        intended diagnostic:
            error: argument color: invalid choice: 'PURPLE'
            (choose from RED, GREEN, BLUE)
    """

    def _convert(s: str) -> enum.Enum:
        try:
            return enum_class[s]
        except KeyError:
            valid = ", ".join(e.name for e in enum_class)
            raise ArgumentTypeError("invalid choice: %r (choose from %s)" % (s, valid))

    return _convert


def _is_sequence_type(arg_type: Any) -> bool:
    """Return True if arg_type is list, tuple, or a generic alias like list[int].

    Args:
        arg_type: the type annotation to inspect
    """
    origin = get_origin(arg_type)
    if origin is not None:
        return origin in (list, tuple)
    return arg_type in (list, tuple)


def _get_element_type(arg_type: Any) -> Callable:
    """Extract the element type from a generic list/tuple annotation.

    Args:
        arg_type: a list or tuple type annotation (e.g. list[int], tuple[str, ...])

    Returns:
        the element type, or str if no element type is specified
    """
    type_args = get_args(arg_type)
    if not type_args:
        return str
    return type_args[0]


def _is_literal_type(arg_type: Any) -> bool:
    """Return True if arg_type is a typing.Literal annotation.

    Args:
        arg_type: the type annotation to inspect
    """
    return get_origin(arg_type) is Literal


def _get_literal_values(arg_type: Any) -> Tuple[Any, ...]:
    """Return the tuple of allowed values from a Literal annotation.

    Args:
        arg_type: a Literal type annotation (e.g. Literal["a", "b"])
    """
    return get_args(arg_type)


def _add_log_level_argument(parser: ArgumentParser):
    parser.add_argument(
        "--log-level", required=False, choices=list(logging._nameToLevel.keys())
    )


def _get_args_name_from_parser(parser: ArgumentParser):
    """Retrieve the name of the function argument linked to the given parser.

    Args:
        parser: a function parser
    """
    # Retrieve the 'action' destination of the method parser i.e. its
    # argument name. The HelpAction is ignored.
    return [
        action.dest
        for action in parser._actions
        if not isinstance(action, _HelpAction) and action.dest != "log_level"
    ]
