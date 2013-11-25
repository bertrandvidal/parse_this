parse_this
==========

Makes it easy to parse command line arguments for any function.

Usage
-----
parse_this can be in two ways:

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
from parse_this import create_parser


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

TODO
----
 * Docstring parsing doesn't handle multiline for argument
 * Handle method rather than just function
 * Handle vargs and kwargs



