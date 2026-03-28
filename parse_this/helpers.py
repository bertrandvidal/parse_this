import enum
import inspect
import logging
from argparse import ArgumentParser, ArgumentTypeError, _HelpAction
from pathlib import PurePath
from typing import Any, Callable, Type

_LOG = logging.getLogger(__name__)


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


def _is_path_type(arg_type: Any) -> bool:
    """Return True if arg_type is a class derived from pathlib.PurePath.

    Args:
        arg_type: the type annotation to inspect

    Note:
        Using PurePath as the base catches Path, PurePath, PosixPath,
        WindowsPath, PurePosixPath, and PureWindowsPath.
    """
    return inspect.isclass(arg_type) and issubclass(arg_type, PurePath)


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
