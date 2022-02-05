from parse_this.exception import ParseThisException
from parse_this.values import Class, Self


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
            "Too many types provided for conversion for '{}'.".format(func_name)
        )
    if len(types) < len(func_args) - len(defaults):
        raise ParseThisException(
            "Not enough types provided for conversion for '{}'".format(func_name)
        )
    if types and types[0] in [Self, Class]:
        types = types[1:]
        func_args = func_args[1:]
    return types, func_args
