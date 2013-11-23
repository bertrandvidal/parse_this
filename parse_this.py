from argparse import ArgumentParser
from inspect import getargspec
from itertools import izip_longest
import sys


class NoDefault(object):
  """Use to fill the list of args and default to indicate the argument doesn't
    have a default value.
  """
  pass


def _get_args_and_defaults(args, defaults):
  """Return a list of 2-tuples - the argument name and its default value or
     a special value that indicates there is no default value.

  Args:
    args: list of argument name
    defaults: tuple of default values
  """
  args_and_defaults = []
  for (k,v) in izip_longest(args[::-1], defaults[::-1], fillvalue=NoDefault):
    args_and_defaults.append((k,v))
  return args_and_defaults[::-1]


def _get_arg_parser(func, types, args_and_defaults):
  """Return an ArgumentParser for the given function. Arguments are defined
    from the method arguments and their associated defaults.

  Args:
    func: method for which we want an ArgumentParser
    types: types to which the command line arguments should be converted to
    args_and_defaults: list of 2-tuples (arg_name, arg_default)
  """
  parser = ArgumentParser(description="Description for '%s'" % func.__name__)
  identity_type = lambda x:x
  for ((arg, default), arg_type) in izip_longest(args_and_defaults, types):
    arg_type = arg_type or identity_type
    if default is NoDefault:
      parser.add_argument(arg, help="Help for %s" % arg, type=arg_type)
    else:
      parser.add_argument("--%s" % arg, help="Help for %s" % arg,
                          default=default, type=arg_type)
  return parser


def _get_args_to_parse(args, sys_argv):
  """Return the given argument if it is not None else sys.argv if it contains
    something, an empty list otherwise.

  Args:
    args: argument to be parsed
    sys_argv: arguments of the command line i.e. sys.argv[1:]
  """
  if args is None:
    command_line_arguments = sys_argv
    if command_line_arguments:
      return command_line_arguments
    return []
  return args


def _check_types(types, func_args, defaults):
  """Make sure that enough types were given to ensure conversion

  Args:
    types: a list of Python types to which the argument should be converted
    func_args: list of function arguments name
    defaults: tuple of default values for the function argument
  """
  if len(types) > len(func_args):
    raise AssertionError("To many types provided for conversion.")
  if len(types) < len(func_args) - len(defaults):
    raise AssertionError("Not enough types provided for conversion")

def parse_this(func, types, args=None):
  (func_args, varargs, keywords, defaults) = getargspec(func)
  _check_types(types, func_args, defaults)
  args_and_default = _get_args_and_defaults(func_args, defaults)
  parser = _get_arg_parser(func, types, args_and_default)
  arguments = parser.parse_args(_get_args_to_parse(args, sys.argv[1:]))
  return arguments

