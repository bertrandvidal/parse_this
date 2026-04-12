import logging
from typing import Callable, Dict, List, Optional, Tuple

from docstring_parser import DocstringStyle, ParseError, parse

from parse_this.exception import ParseThisException

_LOG = logging.getLogger(__name__)

# Public-facing names map to docstring_parser's enum. ``"auto"`` defers
# detection to docstring_parser, which sniffs Google/NumPy/reST/Epytext
# from the docstring's structure.
_STYLE_MAP: Dict[str, DocstringStyle] = {
    "auto": DocstringStyle.AUTO,
    "google": DocstringStyle.GOOGLE,
    "numpy": DocstringStyle.NUMPYDOC,
    "rest": DocstringStyle.REST,
    "epytext": DocstringStyle.EPYDOC,
}


def _get_default_help_message(
    func: Callable,
    args: List[str],
    description: Optional[str] = None,
    args_help: Optional[Dict[str, str]] = None,
) -> Tuple[str, Dict[str, str]]:
    """Create a default description for the parser and help message for the
    arguments if they are missing.

    Args:
        func: the method we are creating a parser for
        args: the argument names of the method
        description: a potentially existing description created from the
        function docstring
        args_help: a dict {arg_name: help} with potentially missing arguments

    Returns:
        a tuple (arg_parse_description, complete_args_help)
    """
    if description is None:
        description = "Argument parsing for %s" % func.__name__
    args_help = args_help or {}
    # If an argument is missing a help message we create a simple one
    for argument in [arg_name for arg_name in args if arg_name not in args_help]:
        args_help[argument] = "Help message for %s" % argument
    return description, args_help


def _collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace (including newlines) into single spaces.

    docstring_parser preserves multiline parameter descriptions with
    embedded newlines. argparse's ``help`` field expects a single line, so
    flatten any continuation lines into one space-joined string.
    """
    return " ".join(text.split())


def prepare_doc(
    func: Callable, args: List[str], style: str = "auto"
) -> Tuple[str, Dict[str, str]]:
    """From the function docstring get the arg parse description and arguments
        help message. If there is no docstring simple description and help
        message are created.

    Args:
        func: the function that needs argument parsing
        args: name of the function arguments
        style: docstring style hint. One of ``"auto"`` (default,
        autodetect), ``"google"``, ``"numpy"``, ``"rest"``, ``"epytext"``.

    Returns:
        A tuple containing the description to be used in the argument parser and
        a dict indexed on the callable argument name and their associated help
        message
    """
    _LOG.debug("Preparing doc for '%s'", func.__name__)
    if not func.__doc__:
        return _get_default_help_message(func, args)
    try:
        ds_style = _STYLE_MAP[style]
    except KeyError:
        raise ParseThisException(
            f"Unknown docstring_style {style!r}. Expected one of {sorted(_STYLE_MAP)}."
        )
    try:
        parsed = parse(func.__doc__, style=ds_style)
    except ParseError:
        # Malformed docstring that no style understood — fall back to
        # auto-generated defaults rather than crashing decoration.
        return _get_default_help_message(func, args)
    description_parts = [
        part for part in (parsed.short_description, parsed.long_description) if part
    ]
    description = _collapse_whitespace(" ".join(description_parts)) or None
    args_help = {
        param.arg_name: _collapse_whitespace(param.description)
        for param in parsed.params
        if param.description
    }
    return _get_default_help_message(func, args, description, args_help)
