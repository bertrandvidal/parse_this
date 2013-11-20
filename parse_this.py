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


def _get_arg_parser(func, args_and_defaults):
  """Return an ArgumentParser for the given function. Arguments are defined
    from the method arguments and their associated defaults.

  Args:
    func: method for which we want an ArgumentParser
    args_and_defaults: list of 2-tuples (arg_name, arg_default)
  """
  parser = ArgumentParser(description="Description for '%s'" % func.__name__)
  for (arg, default) in args_and_defaults:
    if default is NoDefault:
      parser.add_argument(arg, help="Help for %s" % arg)
    else:
      parser.add_argument("--%s" % arg, help="Help for %s" % arg,
                          default=default)
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


def parse_this(func, args=None):
  (func_args, varargs, keywords, defaults) = getargspec(func)
  parser = _get_arg_parser(func, _get_args_and_defaults(func_args, defaults))
  arguments = parser.parse_args(_get_args_to_parse(args, sys.argv[1:]))
  return arguments

