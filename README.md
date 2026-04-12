parse_this
==========

[![PyPI latest version badge][pypi_version]][pypi_link] ![supported python versions][python_version] ![wheel support][wheel_support]

Generate a command line interface for any Python function from its signature
and docstring — no `argparse` boilerplate.


What is parse_this?
-------------------

You wrote a function. Its parameters are named clearly, type-annotated, and
documented in the docstring. Now you want to call it from the command line.
Writing the corresponding `argparse` setup is busywork: every parameter needs
an `add_argument` call with a name, a type, a help message, and a default.

`parse_this` reads the information that's already in your function — its
signature and its docstring — and builds the parser for you. You decorate (or
wrap) your function, you call it, and the right CLI just exists.

`parse_this` exposes three entry points:

* `parse_this(func)` — parse and call a function in one shot
* `@create_parser` — decorator that attaches a `.parser` to a function or method
* `@parse_class` — class decorator that builds a multi-subcommand CLI

Pick the one that matches your use case (the next section gives a one-line
summary of each), then jump to the corresponding section below.


Installation
------------

```bash
pip install parse_this
```

`parse_this` depends on [`docstring-parser`][docstring_parser] for reading
Google, NumPy, reST, and Epytext docstrings. It supports Python 3.10+.

[docstring_parser]: https://pypi.org/project/docstring-parser/


Quick start
-----------

The smallest useful example: a single function turned into a CLI.

```python
# greet.py
from parse_this import create_parser


@create_parser()
def greet(name: str, count: int = 1):
    """Greet someone.

    Args:
        name: who to greet
        count: how many times to repeat the greeting
    """
    return f"Hello, {name}! " * count


if __name__ == "__main__":
    print(greet.parser.call())
```

```bash
python greet.py World
```

```
Hello, World!
```

```bash
python greet.py World --count 3
```

```
Hello, World! Hello, World! Hello, World!
```

```bash
python greet.py --help
```

```
usage: greet.py [-h] [--count COUNT] name

Greet someone.

positional arguments:
  name           who to greet

options:
  -h, --help     show this help message and exit
  --count COUNT  how many times to repeat the greeting
```

That's it. The argument names, types, defaults, and help messages all came
from the function signature and docstring.


The three entry points
----------------------

| Entry point | Use it when... |
|---|---|
| [`parse_this(func)`](#using-parse_this-as-a-function) | You want to parse `sys.argv` and call a function in a single expression, with no decoration. |
| [`@create_parser`](#using-create_parser-as-a-decorator) | You want to attach a CLI to a function or method while still being able to call it normally from Python. |
| [`@parse_class`](#building-a-class-based-cli-with-parse_class) | You want a multi-subcommand CLI where each subcommand maps to a method on a class. |

All three share the same underlying machinery, so the rules for type
annotations, docstring formatting, and argument types are identical across
them. Those rules are documented once, in the [Argument types](#argument-types)
and [Writing docstrings](#writing-docstrings-for-help-messages) sections below.


Using `@create_parser` as a decorator
-------------------------------------

`@create_parser` adds a `.parser` attribute to the decorated function. The
function itself is unchanged — you can still call it normally from Python.

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

```bash
python script.py yes --two 3
```

```
yesyesyes
```

The decorated function is still a regular Python callable:
`concatenate_str("hi", 4)` works as you'd expect.

**Limitation:** `@create_parser` cannot be stacked with other decorators that
modify the function's signature (e.g. anything using `functools.wraps` over a
wrapper that changes the parameters), because it inspects the signature at
decoration time.


Using `parse_this` as a function
--------------------------------

If you don't want to decorate the function, call `parse_this` directly. It
parses `sys.argv` (or an explicit list of arguments), calls the function, and
returns the result.

```python
from parse_this import parse_this


def concatenate_str(one: str, two: int = 2):
    """Concatenates a string with itself a given number of times.

    Args:
        one: string to be concatenated with itself
        two: number of times the string is concatenated, defaults to 2
    """
    return one * two


if __name__ == "__main__":
    print(parse_this(concatenate_str))
```

```bash
python script.py yes --two 3
```

```
yesyesyes
```

You can pass an explicit argument list (useful in tests):

```python
parse_this(concatenate_str, args=["yes", "--two", "3"])
```

```
'yesyesyes'
```


Building a class-based CLI with `@parse_class`
----------------------------------------------

`@parse_class` is for CLIs with multiple subcommands. Each method decorated
with `@create_parser` becomes a subcommand. If `__init__` is also decorated,
its arguments become the *top-level* arguments of the CLI — the ones that come
before the subcommand name.

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
python script.py --help
```

(Prints comprehensive help including all subcommands.)

```bash
python script.py 2 do-stuff 2
```

```
4
```

```bash
python script.py 2 --ham 2 do-stuff 2 --spam 2
```

```
16
```

How it works:

* The class is decorated with `@parse_class`.
* Each method is decorated with `@create_parser`.
* If `__init__` is decorated, its arguments become the top-level CLI arguments.
* All other decorated methods become subcommands.
* Calling `<Class>.parser.call()` parses `sys.argv`, instantiates the class
  from the top-level args, and dispatches the chosen subcommand.

When `--help` is invoked on the top-level parser, the help for **every**
subcommand is shown as well.

### Method names

By default, a method named `do_stuff` becomes the subcommand `do-stuff` —
underscores in method names are replaced with hyphens, which is the more
typical CLI convention.

You can override the name explicitly with `name=`:

```python
@create_parser(name="run")
def do_stuff(self, bar: int):
    ...
```

Now invoked as:

```bash
python script.py 2 run 2
```

**Private methods** (those whose name starts with `_`) are skipped by default.
To include them, pass `parse_private=True` to `@parse_class`. Their leading
and trailing underscores are stripped to form the subcommand name, so:

* `_inner` becomes `inner`
* `__str__` becomes `str`
* `_private_helper` becomes `private-helper`

Note that only **leading and trailing** underscores are stripped — internal
underscores are still converted to hyphens.

### Custom description

By default, the top-level parser's description is taken from the class
docstring. Override it with `description=`:

```python
@parse_class(description="A program for stuff and things.")
class ParseMePlease(object):
    ...
```

### Reusing an existing instance

If you already have an instance of the class and just want `parse_this` to
dispatch the subcommand against it, pass `instance=` to `.parser.call()`:

```python
my_obj = ParseMePlease(foo=2, ham=3)
ParseMePlease.parser.call(instance=my_obj)
```

When `instance` is provided, the top-level (`__init__`) arguments are still
parsed but ignored, since the object already exists. This is mainly useful
when the lifecycle of the object is managed by something other than the CLI.


Classmethods and staticmethods
------------------------------

Classmethods and staticmethods can be parsed, both on their own and as
subcommands inside a `@parse_class`:

```python
from parse_this import create_parser, parse_class


class MyClass(object):

    @classmethod
    @create_parser()
    def parse_me_if_you_can(cls, an_int: int, a_string: str, default: int = 12):
        """I dare you to parse me !!!

        Args:
            an_int: int are pretty cool
            a_string: string aren't that nice
            default: guess what I got a default value
        """
        return a_string * an_int, default * default


MyClass.parse_me_if_you_can.parser.call(MyClass)
```

Inside a `@parse_class`, classmethods and staticmethods become first-class
subcommands. A class whose only parseable methods are classmethods or
staticmethods does not need a decorated `__init__` — `parse_this` dispatches
on the class object directly:

```python
@parse_class()
class Math(object):
    """Simple math operations."""

    @staticmethod
    @create_parser()
    def add(a: int, b: int):
        """Add two integers.

        Args:
            a: first operand
            b: second operand
        """
        return a + b


print(Math.parser.call("add 3 4".split()))
```

```
7
```

Notes:

* The `@classmethod` / `@staticmethod` decorator must be placed **on top**
  of `@create_parser`, otherwise the method won't be a class/static method
  anymore.


Writing docstrings for help messages
------------------------------------

`parse_this` reads the docstring of your function/method to generate the
parser description and per-argument help text displayed by `--help`. Parsing
is delegated to [`docstring-parser`][docstring_parser], which natively
understands the four mainstream Python docstring styles: **Google**,
**NumPy**, **reStructuredText / Sphinx**, and **Epytext**.

By default the style is auto-detected per function — write your docstring in
whichever style your project already uses and it just works. If detection
guesses wrong, pass `docstring_style="<style>"` to lock it explicitly. The
accepted values are `"auto"` (default), `"google"`, `"numpy"`, `"rest"`,
and `"epytext"`. The kwarg is accepted by `parse_this`, `@create_parser`,
and (per-method) inside `@parse_class`.

If you don't provide a docstring at all, `parse_this` falls back to a
generic — and not very useful — help message.

### Google style

```python
@create_parser()
def greet(name: str, count: int = 1):
    """Greet someone.

    Args:
        name: who to greet
        count: how many times to repeat the greeting
    """
    ...
```

The other supported styles are:

* [**NumPy style**](https://numpydoc.readthedocs.io/en/latest/format.html)
* [**reStructuredText / Sphinx style**](https://www.sphinx-doc.org/en/master/usage/restructuredtext/field-lists.html)
* [**Epytext style**](https://epydoc.sourceforge.net/manual-epytext.html)

### Forcing a specific style

If auto-detection guesses wrong, lock the style explicitly:

```python
@create_parser(docstring_style="numpy")
def greet(name: str, count: int = 1):
    ...
```


Argument types
--------------

`parse_this` uses the type annotations on your function to convert command
line strings into the right Python values. Annotations are required for any
required (positional) argument; for optional arguments (those with a default),
the type is inferred from the default value if no annotation is given.

### Basic types

Any Python builtin type works directly: `int`, `str`, `float`, etc.

```python
@create_parser()
def add(a: int, b: int):
    return a + b
```

```bash
python script.py 2 3
```

```
5
```

### `None` as a default value

Using `None` as a default is common Python style, but `parse_this` cannot
infer a type from `None`. You **must** annotate the argument, otherwise a
`ParseThisException` is raised at decoration time. Any of the idiomatic
"optional" annotations work — a concrete type, `Optional[T]`, `Union[T, None]`,
or PEP 604 `T | None`:

```python
from parse_this import create_parser


@create_parser()
def parrot(ham: str, spam: int | None = None):
    if spam is not None:
        return ham * spam
    return ham


print(parrot.parser.call(args=["yes"]))
print(parrot.parser.call(args=["yes", "--spam", "3"]))
```

```
yes
yesyesyes
```

Without the annotation on `spam`, you'd see:

```
ParseThisException: parameter 'spam' of 'parrot' has default None but no
type annotation. Add an annotation, for example: spam: int | None = None
```

`Optional[T]` / `T | None` is unwrapped to `T` before the argument is
registered, so the resulting CLI is identical to using `int = None` — the
only difference is that the `Optional` form is the type-checker-approved
way to express "this argument may be None."

### `bool` flags

`bool` arguments — annotated explicitly or inferred from a `bool` default —
become flags on the command line.

**With a default value**, the flag toggles the default. The most common case
is a `False` default and a `--flag` that turns it on:

```python
@create_parser()
def parrot(ham: str, spam: bool = False):
    if spam:
        return ham, spam
    return ham


print(parrot.parser.call(args=["yes"]))
print(parrot.parser.call(args=["yes", "--spam"]))
```

```
yes
('yes', True)
```

**Without a default**, the implicit default is `True`, and the flag turns it
off:

```python
@create_parser()
def parrot(ham: str, spam: bool):
    return ham, spam


print(parrot.parser.call(args=["yes"]))
print(parrot.parser.call(args=["yes", "--spam"]))
```

```
('yes', True)
('yes', False)
```

### Enum arguments

Parameters annotated with an `enum.Enum` subclass become restricted choices on
the command line. The member **name** (not its value) is used as the CLI
token, and `parse_this` converts it back to the enum member before calling
your function.

```python
import enum
from parse_this import create_parser


class Color(enum.Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


@create_parser()
def paint(color: Color, canvas: str = "wall"):
    """Paint something.

    Args:
        color: the color to use
        canvas: what to paint
    """
    return color, canvas
```

```bash
python script.py RED
```

```
(<Color.RED: 1>, 'wall')
```

```bash
python script.py GREEN --canvas fence
```

```
(<Color.GREEN: 2>, 'fence')
```

```bash
python script.py PURPLE
```

```
usage: script.py [-h] [--canvas CANVAS] {RED,GREEN,BLUE}
script.py: error: argument {RED,GREEN,BLUE}: invalid choice: 'PURPLE' (choose from RED, GREEN, BLUE)
```

Optional enum arguments work the same way, with the default supplied as an
enum member:

```python
@create_parser()
def spray(canvas: str, color: Color = Color.BLUE):
    return canvas, color


print(spray.parser.call(args=["fence"]))
print(spray.parser.call(args=["fence", "--color", "RED"]))
```

```
('fence', <Color.BLUE: 3>)
('fence', <Color.RED: 1>)
```

The `--help` output shows the valid member names, e.g. `{RED,GREEN,BLUE}`.

### `Literal` arguments

Parameters annotated with `typing.Literal` become restricted choices, with the
allowed values taken directly from the annotation. The element type is
preserved, so `Literal[1, 2, 3]` expects integers, not strings.

```python
from typing import Literal
from parse_this import create_parser


@create_parser()
def deploy(env: Literal["dev", "staging", "prod"], mode: Literal["full", "quick"] = "quick"):
    """Deploy the app.

    Args:
        env: target environment
        mode: deployment mode
    """
    return env, mode
```

```bash
python script.py dev
```

```
('dev', 'quick')
```

```bash
python script.py staging --mode full
```

```
('staging', 'full')
```

```bash
python script.py local
```

```
usage: script.py [-h] [--mode {full,quick}] {dev,staging,prod}
script.py: error: argument env: invalid choice: 'local' (choose from dev, staging, prod)
```

All values in a single `Literal` must share the same type — mixed types like
`Literal[1, "auto"]` raise a `ParseThisException` at decoration time. A
default value that isn't one of the listed values also raises
`ParseThisException`.

### List and tuple arguments

Parameters annotated with `list[T]` or `tuple[T, ...]` are turned into
multi-value arguments using argparse's `nargs="+"` (one or more values). Each
value is converted to the element type `T`.

```python
from parse_this import create_parser


@create_parser()
def total(values: list[int]):
    """Sum a list of integers.

    Args:
        values: one or more integers to sum
    """
    return sum(values)
```

```bash
python script.py 1 2 3
```

```
6
```

```bash
python script.py 10
```

```
10
```

Optional list/tuple arguments use a `--flag`:

```python
@create_parser()
def greet(name: str, titles: list[str] = None):
    """Greet with optional titles.

    Args:
        name: person to greet
        titles: optional list of titles
    """
    return name, titles
```

```bash
python script.py Alice
```

```
('Alice', None)
```

```bash
python script.py Alice --titles Dr Prof
```

```
('Alice', ['Dr', 'Prof'])
```

`tuple[T, ...]` works identically — note that argparse always returns a
`list`, even when the annotation is a tuple. If no element type is specified
(bare `list` or `tuple`), values are treated as strings.

### Variadic positional arguments (`*args`)

Functions with `*args` are supported: the variadic parameter becomes a
trailing positional argument using argparse's `nargs="*"` (zero or more
values). The element type comes from the annotation (or defaults to
`str`):

```python
from parse_this import create_parser


@create_parser()
def total(*nums: int):
    """Sum integers.

    Args:
        nums: integers to sum
    """
    return sum(nums)
```

```bash
python script.py 1 2 3
```

```
6
```

`*args` composes with regular positional and optional parameters as long
as optional parameters appear **before** `*args` in the signature (Python
keyword-only parameters, which appear after `*args`, are not currently
exposed to the parser). `**kwargs` is rejected at decoration time with a
`ParseThisException`, since argparse has no notion of arbitrary key/value
flags.


Optional features
-----------------

### `--log-level`

All three entry points accept a `log_level=True` keyword argument. When set,
an optional `--log-level` argument is added to the command line, with choices
matching the standard `logging` level names (`DEBUG`, `INFO`, `WARNING`,
`ERROR`, `CRITICAL`, etc.).

If `--log-level` is passed, `logging.basicConfig(level=...)` is called before
your function runs. The `--log-level` argument is automatically excluded from
the arguments passed to your function — you don't need to declare it in your
signature.

```python
from parse_this import create_parser


@create_parser(log_level=True)
def greet(name: str, count: int = 1):
    """Greet someone.

    Args:
        name: who to greet
        count: how many times
    """
    import logging
    logging.debug("About to greet %s %d time(s)", name, count)
    return f"Hello, {name}! " * count
```

```bash
python script.py Alice
```

```
Hello, Alice!
```

```bash
python script.py Alice --log-level DEBUG
```

```
DEBUG:root:About to greet Alice 1 time(s)
Hello, Alice!
```

```bash
python script.py Alice --count 3 --log-level INFO
```

```
Hello, Alice! Hello, Alice! Hello, Alice!
```

For `@parse_class`, `--log-level` is added to the **top-level** parser:

```python
from parse_this import create_parser, parse_class


@parse_class(log_level=True)
class MyApp(object):
    """My application."""

    @create_parser()
    def __init__(self):
        """Init."""

    @create_parser()
    def run(self, task: str):
        """Run a task.

        Args:
            task: task name
        """
        return task
```

```bash
python script.py --log-level DEBUG run my-task
```

```
my-task
```

### `--version`

`parse_this` and `@parse_class` accept an optional `version=` keyword
argument. When provided, a `--version` flag is added that prints the string
and exits.

```python
from parse_this import parse_class, create_parser


@parse_class(version="1.2.3")
class MyApp(object):
    """My application."""

    @create_parser()
    def __init__(self):
        """Init."""

    @create_parser()
    def run(self, task: str):
        """Run a task.

        Args:
            task: task name
        """
        return task


if __name__ == "__main__":
    print(MyApp.parser.call())
```

```bash
python script.py --version
```

```
1.2.3
```

For functions, the same pattern works with `parse_this`:

```python
from parse_this import parse_this


def greet(name: str):
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(parse_this(greet, version="1.2.3"))
```

The recommended way to source the version is
`importlib.metadata.version("your-package-name")`, which reads it from your
installed package metadata (i.e. from `pyproject.toml` at install time) so the
literal does not need to be kept in sync by hand:

```python
from importlib.metadata import version

@parse_class(version=version("your-package-name"))
class MyApp(object):
    ...
```

argparse also supports `%(prog)s` substitution in the version string, which
expands to the program name:

```python
@parse_class(version="%(prog)s 1.2.3")
class MyApp(object):
    ...
```

```bash
python script.py --version
```

```
script.py 1.2.3
```

**Note:** `@create_parser` does **not** accept a `version` argument. When a
method decorated with `@create_parser` is used as a subcommand inside a
`@parse_class`, argparse's `parents` mechanism would copy the `--version`
action onto every subcommand, producing CLIs like
`python script.py 2 do-stuff --version`. Put `version=` on the top-level
`@parse_class` (or `parse_this`) instead.


Errors
------

`parse_this` raises a single exception type, `ParseThisException`, which is a
subclass of `Exception`. You can import it from the package directly:

```python
from parse_this import ParseThisException
```

It is raised in the following situations, all of them at decoration time —
that is, when the script is loaded, not when the CLI is invoked:

* **A required argument has no type annotation.** Required (positional)
  arguments must have an annotation; the type cannot be inferred from
  anything else.
* **An optional argument has `None` as a default value but no annotation.**
  See the [`None` as a default](#none-as-a-default-value) section.
* **A `Union` annotation has more than one non-`None` arm** (e.g.
  `Union[int, str]`). `parse_this` cannot pick which converter to use — use
  a single concrete type or `Optional[T]`.
* **A `Literal` annotation has values of mixed types** (e.g.
  `Literal[1, "auto"]`). All values must share the same type.
* **A `Literal` argument's default is not one of the listed values**, e.g.
  `mode: Literal["a", "b"] = "c"`.
* **`@create_parser` is used on `__init__` outside of a `@parse_class`.**
  Decorating `__init__` only makes sense as part of a class-based CLI; the
  exception is raised when you try to invoke
  `<Class>.__init__.parser.call()` directly.
* **The decorated function has a `**kwargs` parameter.** `parse_this`
  cannot build argparse flags from arbitrary keyword arguments — either
  remove the `**kwargs` parameter or expose specific options as explicit
  parameters.

Argparse's own errors (invalid choices, missing required args, type
conversion failures) are raised by argparse itself and not wrapped — they
behave the same as in any other argparse-based CLI.


Caveats and limitations
-----------------------

* Keyword-only parameters (arguments declared after `*args`) are not
  exposed to the parser. Place optional flags before `*args` in the
  signature.


Development
-----------

To set up a development environment:

```sh
python3 -m venv --clear --upgrade-deps --prompt "parse-this" venv && \
source venv/bin/activate && \
pip install -e ".[dev]" && \
pre-commit install && \
pytest
```

Run the test suite at any time with `pytest`. The project uses `ruff` and
`mypy` via `pre-commit`, so you don't need to invoke them manually.

### Releasing

Update the version of the package in `pyproject.toml` and merge it to `main`
via PR. The package is built, `main` is tagged with the version, a GitHub
release is created, and the package is uploaded to pypi.org via trusted
publishing.


License
-------

`parse_this` is released under the MIT Licence. See the bundled LICENSE file
for details.


[pypi_link]: https://pypi.org/project/parse-this/ "parse_this on PyPI"
[pypi_version]: https://badge.fury.io/py/parse-this.svg "PyPI latest version"
[python_version]: https://img.shields.io/pypi/pyversions/parse_this?style=flat-square
[wheel_support]: https://img.shields.io/pypi/wheel/parse_this?style=flat-square
