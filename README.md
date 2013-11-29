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

```python
from parse_this import create_parser


class INeedParsing(object):

  @create_parser(int, str)
  def parse_me_if_you_can(self, an_int, a_string, default=12):
   return a_string * an_int, default * default


if __name__ == "__main__":
  need_parsing = INeedParsing()
  parser = need_parsing.parse_me_if_you_can.parser
  namespace_args = parser.parse_args()
  print need_parsing.parse_me_if_you_can(namespace_args.an_int,
					 namespace_args.a_string)
```


TODO
----
 * Docstring parsing doesn't handle multiline for argument
 * Handle vargs and kwargs



