parse_this
==========

Makes it easy to parse command line arguments for any function, method or classmethod.

Usage
-----

### Decorator
As a decorator that will create an argument parser for the decorated function.
A `parser` attribute will be added to the method and can be used to parse the
command line argument.

```python
from parse_this import create_parser


@create_parser(str, int)
def concatenate_str(one, two=2):
  """Concatenates a string with itself a given number of times.

  Args:
    one: string to be concatenated with itself
    two: number of times the string is concatenated, defaults to 2
  """
  return one * two


if __name__ == "__main__":
  parser = concatenate_str.parser
  namespace_args = parser.parse_args()
  print concatenate_str(namespace_args.one, namespace_args.two)
```

Note that the function can still be called as any other function.

### Function
As a function that will handle the command line arguments directly.

```python
from parse_this import parse_this


def concatenate_str(one, two=2):
  """Concatenates a string with itself a given number of times.

  Args:
    one: string to be concatenated with itself
    two: number of times the string is concatenated, defaults to 2
  """
  return one * two


if __name__ == "__main__":
  print parse_this(concatenate_str, [str, int])
```

Arguments and types
-------------------

Both `parse_this` and `create_parser` need a list of types to which
arguments will be converted to. Any Python type can be used, two
special values are used for the `self` and `cls` respectively `Self`
and `Class`. There is no need to provide a type for keyword agurment
since it is infered from the default value of the argument.

If this is the containt of `test.py`:
```python
from parse_this import create_parser, Self


class INeedParsing(object):

  @create_parser(Self, int, str)
  def parse_me_if_you_can(self, an_int, a_string, default=12):
   """I dare you to parse me !!!

   Args:q:"
     an_int: int are pretty cool
     a_string: string aren't that nice
     default: guess what I got a default value
   """
   return a_string * an_int, default * default


if __name__ == "__main__":
  need_parsing = INeedParsing()
  parser = need_parsing.parse_me_if_you_can.parser
  namespace_args = parser.parse_args()
  print need_parsing.parse_me_if_you_can(namespace_args.an_int,
                     namespace_args.a_string)
```

The following would be the output of the command line `python test.py --help`:

```bash
usage: test.py [-h] [--default DEFAULT] an_int a_string

I dare you to parse me !!!

positional arguments:
  an_int             int are pretty cool
  a_string           string aren't that nice

optional arguments:
  -h, --help         show this help message and exit
  --default DEFAULT  guess what I got a default value
```

TODO
----
 * Docstring parsing doesn't handle multiline for argument
 * Handle vargs and kwargs
 * Make a package and upload it to pypy


