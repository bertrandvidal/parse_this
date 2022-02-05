import logging
import re

_LOG = logging.getLogger(__name__)


def _get_default_help_message(func, args, description=None, args_help=None):
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


def prepare_doc(func, args, delimiter_chars):
    """From the function docstring get the arg parse description and arguments
        help message. If there is no docstring simple description and help
        message are created.

    Args:
        func: the function that needs argument parsing
        args: name of the function arguments
        delimiter_chars: characters used to separate the parameters from their
        help message in the docstring

    Returns:
        A tuple containing the description to be used in the argument parser and
        a dict indexed on the callable argument name and their associated help
        message
    """
    _LOG.debug("Preparing doc for '%s'", func.__name__)
    if not func.__doc__:
        return _get_default_help_message(func, args)
    description = []
    args_help = {}
    fill_description = True
    arg_name = None
    arg_doc_regex = re.compile(
        "\b*(?P<arg_name>\w+)\s*%s\s*(?P<help_msg>.+)" % delimiter_chars  # noqa: W605
    )
    for line in func.__doc__.splitlines():
        line = line.strip()
        if line and fill_description:
            description.append(line)
        elif line:
            arg_match = arg_doc_regex.match(line)
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
    return _get_default_help_message(func, args, " ".join(description), args_help)
