parse_this
==========

[![PyPI latest version badge][pypi_version]][pypi_link] ![supported python versions][python_version] ![wheel support][wheel_support]

Makes it easy to parse command line arguments for any function, method or classmethod.

You just finished writing an awesome piece of code and now comes the boring part: adding the command line parsing to
actually use it ...

So now you need to use the awesome, but very verbose, `argparse` module. For each argument of your entry point method
you need to add a name, a help message and/or a default value. But wait... Your parameters are correctly named, right!?
They also have type hinting, right!? And you have an awesome docstring for that method. There is probably a way of
creating the `ArgumentParser` easily right?

Yes and it's called `parse_this`!

Usage
-----

`parse_this` contains a simple way to create a command line interface from an entire class. For that you will need to
use the `parse_class` class decorator.

```python
# script.py
from parse_this import create_parser, parse_class


@parse_class()
class ParseMePlease(object):
    """This will be the description of the parser."""

    @create_parser()
    def __init__(self, foo: int, ham: int = 1):
        """Get ready to be parsed!

        Args:
          foo: because naming stuff is hard
          ham: ham is good and it defaults to 1
        """
        self._foo = foo
        self._ham = ham

    @create_parser()
    def do_stuff(self, bar: int, spam: int = 1):
        """Can do incredible stuff with bar and spam.

        Args:
          bar: as in foobar, will be multiplied with everything else
          spam: goes well with eggs, spam, bacon, spam, sausage and spam

        Returns:
          Everything multiplied with each others
        """
        return self._foo * self._ham * bar * spam


if __name__ == "__main__":
    print(ParseMePlease.parser.call())
```


```bash
python script.py --help # Print a comprehensive help and usage message
python script.py 2 do-stuff 2
>>> 4
python script.py 2 --ham 2 do-stuff 2 --spam 2
>>> 16
```

How does it work **TL;DR version**?

* You need to decorate the methods you want to be usable from the command line  using `create_parser`.
* The `__init__` method arguments and keyword arguments will be the arguments and options of the script command line *i.e.* the first arguments and options
* The other methods will be transformed into sub-command, again mapping the command line arguments and options to the method's own arguments
* All you have to do for this to work is:
  * Decorate your class with `parse_class`
  * Decorate methods with `create_parser`
  * Document your class and method with properly formed docstring to get help and usage message
  * Annotate all parameters with their type
  * Call `<YourClass>.parser.call()` and you are done!


If you feel like you may need more customization and details, please read on!

* If the `__init__` method is decorated it will be considered the first, or top-level, parser this means that all
  arguments in your `__init__` will be arguments pass right after invoking you script
  i.e. `python script.py init_arg_1 init_arg_2 etc...`
* The description of the top-level parser is taken from the class's docstring or overwritten by the keyword
  argument `description` of `parse_class`.
* Each method decorated with `create_parser` will become a subparser of its own.
* The command name of the subparser is the same as the method name with `_` replaced by `-`.
* 'Private' methods, whose name start with an `_`, do not have a subparser by default, as this would expose them to the
  outside. However if you want to expose them you can set the keyword argument `parse_private=True` in `parse_class`. If
  exposed their command name will not contain the leading `-` as this would be confusing for command parsing. Special
  methods, such as `__str__`, can be decorated as well. Their command name will be stripped of all `_`s resulting in
  command names such as `str`.
* When used in a `parse_class` decorated class `create_parser` can take an extra parameters `name` that will be used as
  the sub-command name. The same modifications are made to the `name` replacing `_` with `-`
* When calling `python script.py --help` the help message for **every** parser will be displayed making easier to find
  what you are looking for


Arguments and types
-------------------

Both `parse_this` and `create_parser` need parameters to have type annotations. Any Python builtin type can be used.
There is no need to provide a type for keyword arguments since it is inferred from the default value of the argument. If
your method signature contains `arg_with_default=12` `parse_this` expect an `int` where `arg_with_default` is on the
command line.

If this is the content of `parse_me.py`:

```python
from parse_this import create_parser


class INeedParsing(object):
    """A class that clearly needs argument parsing!"""

    def __init__(self, an_argument):
        self._an_arg = an_argument

    @create_parser(delimiter_chars="--")
    def parse_me_if_you_can(self, an_int: int, a_string: str, an_other_int: int = 12):
        """I dare you to parse me !!!

        Args:
            an_int -- int are pretty cool
            a_string -- string aren't that nice
            an_other_int -- guess what? I got a default value
        """
        return a_string * an_int, an_other_int * self._an_arg


if __name__ == "__main__":
    need_parsing = INeedParsing(2)
    print(INeedParsing.parse_me_if_you_can.parser.call(need_parsing))
```

The following would be the output of the command line `python parse_me.py --help`:

```bash
usage: parse_me.py [-h] [--an_other_int AN_OTHER_INT] an_int a_string

I dare you to parse me !!!

positional arguments:
  an_int                int are pretty cool
  a_string              string aren't that nice

optional arguments:
  -h, --help            show this help message and exit
  --an_other_int AN_OTHER_INT
                        guess what? I got a default value
```

The method `parse_me_if_you_can` expect an `int` with the name `an_int`, a `str` with the name `a_string` and
other `int` with the name `an_other_int` and a default value of 12. So does the parser as displayed by the `--help`
command.

Note: `create_parser` cannot decorate the `__init__` method of a class unless the class is itself decorated
with `parse_class`. A `ParseThisException` will be raised if you attempt to use the `call` method of such a parser.


The following would be the output of the command line `python parse_me.py 2 yes --default 4`:

```bash
('yesyes', 8)
```


Help message
------------

In order to get a help message generated automatically from the method docstring
it needs to be in the specific format described below:

```python
from parse_this import create_parser


@create_parser(delimiter_chars="--")
def method(self, spam: int, ham: int):
    """<description>
      <blank_line>
      <arg_name><delimiter_chars><arg_help>
      <arg_name><delimiter_chars><arg_help>
    """
    pass
```

* description: is a multiline description of the method used for the command line
* each line of argument help have the following component:
    * arg_name: the **same** name as the argument of the method.
    * delimiter_chars: one or more chars that separate the argument and its help message. Using whitespaces is not
      recommended as it could have an expected behavior with multiline help message.
    * arg_help: is everything behind the delimiter_chars until the next argument, **a blank line** or the end of the
      docstring.

The `delimiter_chars` can be passed to both `parse_this` and `create_parser` as the keywords argument `delimiter_chars`.
It defaults to `:` since this is the convention I most often use.

If no docstring is specified a generic - not so useful - help message will be generated for the command line and
arguments.


Using None as a default value and bool as flags
-----------------------------------------------

Using `None` as a default value is common practice in Python but for `parse_this` and `create_parser` to work properly
the type of the argument which defaults to `None` needs to be specified. Otherwise a `ParseThisException` will be
raised.

```python
from parse_this import create_parser


@create_parser()
def parrot(ham: str, spam=None):
    if spam is not None:
        return ham * spam
    return ham

# Will raise ParseThisException: To use default value of 'None' you need to specify
# the type of the argument 'spam' for the method 'parrot'
```

Specifying the type of `spam` will allow `create_parser` to work properly

```python
from parse_this import create_parser


@create_parser()
def parrot(ham: str, spam: int = None):
    if spam is not None:
        return ham * spam
    return ham

# Calling function.parser.call(args="yes".split()) -> 'yes'
# Calling function.parser.call(args="yes --spam 3".split()) -> 'yesyesyes'
```

An other common practice is to use `bool`s as flags or switches. All arguments of type `bool`, either typed directly or
inferred from the default value, will become optional arguments of the command line. A `bool` argument without default
value will default to `True` as in the following example:

```python
from parse_this import create_parser

@create_parser()
def parrot(ham: str, spam: bool):
  if spam:
    return ham, spam
  return ham

# Calling parrot.parser.call(args="yes".split()) -> 'yes', True
# Calling parrot.parser.call(args="yes --spam".split()) -> 'yes'
```

Adding `--spam` to the arguments will act as a flag/switch setting `spam` to `False`. Note that `spam` as become
optional and will be given the value `True` if `--spam` is not among the arguments to parse.


Arguments with a boolean default value will act as a flag to change the default value:
```python
from parse_this import create_parser


@create_parser()
def parrot(ham: str, spam: bool = False):
    if spam:
        return ham, spam
    return ham

# Calling parrot.parser.call(args="yes".split()) -> 'yes'
# Calling parrot.parser.call(args="yes --spam".split()) -> ('yes', True)
```

Here everything works as intended and the default value for `spam` is `False`
and passing `--spam` as an argument to be parsed will assign it `True`.


Decorator
---------

As a decorator `create_parser` will create an argument parser for the decorated function. A `parser` attribute will be
added to the method and can be used to parse the command line argument.

```python
from parse_this import create_parser


@create_parser()
def concatenate_str(one: str, two: int = 2):
    """Concatenates a string with itself a given number of times.

    Args:
        one: string to be concatenated with itself
        two: number of times the string is concatenated, defaults to 2
    """
    return one * two


if __name__ == "__main__":
    print(concatenate_str.parser.call())
```

Calling this script from the command line, `python script.py yes --two 3` will return `'yesyesyes'` as expected and all
the parsing has been done for you.

Note that the function can still be called as any other function from any python file. Also it is **not** possible to
stack `create_parser` with any decorator that would modify the signature of the decorated function e.g.
using `functools.wraps`.


Function
--------

As a function `parse_this` will handle the command line arguments directly.

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
    print(parse_this(concatenate_str))
```

Calling this script with the same command line arguments `yes --two 3` will also return `'yesyesyes'` as expected.


Classmethods
------------

In a similar fashion you can parse command line arguments for classmethods:

```python
from parse_this import create_parser


class MyClass(object):

    @classmethod
    @create_parser(delimiter_chars="--")
    def parse_me_if_you_can(cls, an_int: int, a_string: str, default: int = 12):
        """I dare you to parse me !!!

        Args:
            an_int -- int are pretty cool
            a_string -- string aren't that nice
            default -- guess what I got a default value
        """
        return a_string * an_int, default * default


MyClass.parse_me_if_you_can.parser.call(MyClass)
```

The output will be the same as using `create_parser` on a regular method.

**Notes**:

* The `classmethod` decorator is placed **on top** of the `create_parser` decorator in order for the method to still be
  a considered a class method.
* A `classmethod` decorated with `create_parser` in a class decorated with `parse_class` will not be accessible through
  the class command line.


Installing `parse_this`
-----------------------

`parse_this` can be installed using the following command:

```bash
pip install parse_this
```


RUNNING TESTS
-------------

To check that everything is running fine you can run the following command after cloning the repo:

```bash
python -m pip install --upgrade pip && python -m pip install -r requirements.txt && pytest
```

CAVEATS
-------

* `parse_this` and `create_parser` are not able to be used on methods with `*args` and `**kwargs`
* A subsequent effect of the previous caveat is that `create_parser` cannot be stacked with other decorator that would
  alter the callable's signature
* Classmethods cannot be access from the command line in a class decorated with `parse_class`
* When using `create_parser` on a method that has an argument with `None` as a default value its type *must be* past in
  the list of types. A `ParseThisException` will be raised otherwise.

TO DO
-----
  * Handle file arguments
  * Handle list/tuple arguments i.e. argparse's nargs


License
-------

`parse_this` is released under the MIT Licence. See the bundled LICENSE file for details.


Contributing and dev
--------------------

```sh
python3 -m venv --clear --upgrade-deps --prompt "parse-this-39" venv && \
source venv/bin/activate && \
pip install -r requirements.txt && \
pre-commit install && \
pytest
```

[pypi_link]: https://pypi.org/project/parse-this/ "parse_this on PyPI"
[pypi_version]: https://badge.fury.io/py/parse-this.svg "PyPI latest version"
[python_version]: https://img.shields.io/pypi/pyversions/parse_this?style=flat-square
[wheel_support]: https://img.shields.io/pypi/wheel/parse_this?style=flat-square
[inspect_signature]: https://docs.python.org/dev/library/inspect.html#inspect.signature
