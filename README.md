parse_this
==========

[![PyPI latest version badge][pypi_version]][pypi_link] [![Code health][landscape]][landscape_link]

Makes it easy to parse command line arguments for any function, method or classmethod.

You just finished writing an awesome piece of code and now comes the boring part:
adding the command line parsing to actually use it ...

So now you need to use the awesome, but very verbose, `argparse` module.
For each argument of your entry point method you need to add a name, a help
message and/or a default value. But wait... Your parameters are correctly named
right!? And you have an awesome docstring for that method. There is probably a
way of creating the `ArgumentParser` easily right?

Yes and it's called `parse_this`!

Usage
-----

`parse_this` contains a simple way to create a command line interface from an
entire class. For that you will need to use the `parse_class` class decorator.

```python
# script.py
from __future__ import print_function
from parse_this import Self, create_parser, parse_class


@parse_class()
class ParseMePlease(object):
    """This will be the description of the parser."""

    @create_parser(Self, int)
    def __init__(self, foo, ham=1):
        """Get ready to be parsed!

        Args:
          foo: because naming stuff is hard
          ham: ham is good and it defaults to 1
        """
        self._foo = foo
        self._ham = ham

    @create_parser(Self, int, int)
    def do_stuff(self, bar, spam=1):
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

* You need to decorate the methods you want to be usable from the command line
  using `create_parser`.
* The `__init__` method arguments and keyword arguments will be the arguments
  and options of the script command line *i.e.* the first arguments and options
* The other methods will be transformed into sub-command, again mapping the
  command line arguments and options to the method's own arguments
* All you have to do for this to work is:
  * Decorate your class with `parse_class`
  * Decorate methods with `create_parser` making it aware of the type of the
    arguments. Using `Self` to designate the `self` parameter
  * Document your class and method with properly formed docstring to get help
    and usage message
  * Call `<YourClass>.parser.call()` and you are done!


If you feel like you may need more customization and details, please read on!

* If the `__init__` method is decorated it will be considered the first, or
  top-level, parser this means that all arguments in your `__init__` will be
  arguments pass right after invoking you script i.e.
  `python script.py init_arg_1 init_arg_2 etc...`
* The description of the top-level parser is taken from the class's docstring or
  overwritten by the keyword argument `description` of `parse_class`.
* Each method decorated by `create_parser` will become a subparser of its own.
  The command name of the subparser is the same as the method name with `_`
  replaced by `-`. 'Private' methods, whose name start with an `_`, do not have
  a subparser by default, as this would expose them to the outside. However if you
  want to expose them you can set the keyword argument `parse_private=True` to
  `parse_class`. If exposed their command name will not contain the leading `-`
  as this would be confusing for command parsing
* When calling `python script.py --help` the help message for **every** parser
  will be displayed making easier to find what you are looking for
* When used in a `parse_class` decorated class `create_parser` can take an extra
  parameters `name` that will be used as the sub-command name. The same
  modifications are made to the `name` replacing `_` with `_`


###Arguments and types

Both `parse_this` and `create_parser` need a list of types to which arguments
will be converted to. Any Python standard type can be used, two special values
are used for the `self` and `cls` respectively `Self` and `Class`.
There is no need to provide a type for keyword agurments since it is infered
from the default value of the argument. If your method signature contains
`arg_with_default=12` `parse_this` expect an `int` where `arg_with_default` is.

If this is the containt of `test.py`:

```python
from __future__ import print_function
from parse_this import create_parser, Self


class INeedParsing(object):
    """A class that clearly needs argument parsing!"""

    def __init__(self, an_argument):
        self._an_arg = an_argument

    @create_parser(Self, int, str, params_delim="--")
    def parse_me_if_you_can(self, an_int, a_string, an_other_int=12):
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

The following would be the output of the command line `python test.py --help`:

```bash
usage: test.py [-h] [--an_other_int AN_OTHER_INT] an_int a_string

I dare you to parse me !!!

positional arguments:
  an_int             int are pretty cool
  a_string           string aren't that nice

optional arguments:
  -h, --help         show this help message and exit
  --an_other_int AN_OTHER_INT  guess what? I got a default value
```

The method `parse_me_if_you_can` expect an `int` of the name `an_int`, a `str`
of the name `a_string` and other `int` with the name `an_other_int` and a default
value of 12. So does the parser !!! As displayed by the `--help` command.

Note: `create_parser` cannot decorate the `__init__` method of a class unless
the class is itself decorated with `parse_class`. A `ParseThisError` will be
raised if you attempt to use the `call` method of such a parser.


The following would be the output of the command line `python test.py 2 yes --default 4`:

```bash
('yesyes', 8)
```


###Help message

In order to get a help message generated automatically from the method docstring
it needs to be in a specific format as describe below:

```python
...
    @create_parser(Self, int, int, params_delim=<delimiter_chars>)
    def method(self, spam, ham):
    """<description>
    <blank_line>
    <arg_name><delimiter_chars><arg_help>
    <arg_name><delimiter_chars><arg_help>
    """
    pass
...
```

* description: is a multiline description of the method used for the command line
* each line of argument help have the following component:
  * arg_name: the **same** name as the argument of the method
  * delimiter_chars: one or more chars that separate the argument and its help
    message
  * arg_help: is everything behind the delimiter_chars until the next argument,
    **a blank line** or the end of the docstring

The `delimiter_chars` can be passed to both `parse_this` and `create_parser` as
the keywords argument `params_delim`. It defaults to `:` since this is the
convention I most often use.

If no docstring is specified a generic - not so useful - help message will
be generated for the command line and arguments.


Decorator
---------

As a decorator `create_parser` will create an argument parser for a decorated
function. A `parser` attribute will be added to the method and can be used to
parse the command line argument.

```python
from __future__ import print_function
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
    # This parser expect two arguments 'one' and '--two' just like the method
    namespace_args = parser.parse_args()
    print(concatenate_str(namespace_args.one, namespace_args.two))
```

Calling this script from the command line as follow:

```bash
python script.py yes --two 2
```

will return `'yesyes'` as expected and all the parsing have been done for you.

Note that the function can still be called as any other function from any python
file. Also it is not possible to stack `create_parser` with any decorator that
would modify the signature of the decorated function e.g. using `functools.wraps`.


Function
--------

As a function `parse_this` will handle the command line arguments directly.

```python
from __future__ import print_function
from parse_this import parse_this


def concatenate_str(one, two=2):
    """Concatenates a string with itself a given number of times.

    Args:
        one: string to be concatenated with itself
        two: number of times the string is concatenated, defaults to 2
    """
    return one * two


if __name__ == "__main__":
    print(parse_this(concatenate_str, [str, int]))
```

Calling this script with the same command line arguments `yes --two 2` will also
return `'yesyes'` as expected.


Classmethods
------------

In a similar fashion you can parse line arguments for classmethods:

```python

class MyClass(object):
...
    @classmethod
    @create_parser(Class, int, str, params_delim="--")
    def parse_me_if_you_can(cls, an_int, a_string, default=12):
        """I dare you to parse me !!!

        Args:
            an_int -- int are pretty cool
            a_string -- string aren't that nice
            default -- guess what I got a default value
        """
        return a_string * an_int, default * default
...

MyClass.parse_me_if_you_can.parser.call(MyClass)

```
The output will be the same as using `create_parser` on a regular method.
The only difference is the use of the special value `Class` to specify where
the `cls` argument is used.

**Note**: The `classmethod` decorator is placed **on top** of the `create_parser`
decorator in order for the method to still be a considered a class method.


INSTALLING PARSE_THIS
---------------------

`parse_this` can be installed using the following command:

```bash
pip install parse_this
```
or
```bash
easy_install parse_this
```


RUNNING TESTS
-------------

To check that everything is running fine you can run the following command:

```bash
python setup.py nosetests
```


CAVEATS
-------

 * `parse_this` and `create_parser` are not able to be used on methods with
   `*args` and `**kwargs`
 * Classmethods cannot be access from the command line in a class decorated
   with `parse_class`
 * When using `create_parser` on a method that has an argument with `None` as
   a default value its type *must be* past in the list of types.


LICENSE
-------

`parse_this` is released under the MIT Licence. See the bundled LICENSE file for details.


TODO
----
 * Handle vargs and kwargs - if possible
 * Test decorated classmethods in decorated class
 * Reorganize the project in several files - it's starting to get messy.
   Including the test file.
 * Some default values for paramters e.g. `None`, [], {} will not be usable.
   Warns the user when creating the parser.


[pypi_link]: https://pypi.python.org/pypi/parse_this "parse_this on PyPI"
[pypi_version]: https://badge.fury.io/py/parse_this.svg "PyPI latest version"
[landscape_link]: https://landscape.io/github/bertrandvidal/parse_this/master "parse_this on Landscape"
[landscape]: https://landscape.io/github/bertrandvidal/parse_this/master/landscape.png "Code health"
