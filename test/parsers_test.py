import functools
import unittest
from unittest.mock import patch

from parse_this import create_parser, parse_class
from parse_this.exception import ParseThisException
from parse_this.parsers import FunctionParser
from test.helpers import (
    ClassAndStaticMethods,
    Dummy,
    NeedInitDecorator,
    NeedParseClassDecorator,
    NeedParsing,
    OnlyClassMethods,
    ParseableWithLogLevel,
    ShowMyDocstring,
    SubCmdParseError,
    function_with_log_level,
    i_am_parseable,
    parse_me_full_docstring,
    ParseMyInitOnly,
)
from test.utils import captured_output


class TestFunctionParser(unittest.TestCase):
    def test_function_return(self):
        parser = FunctionParser()
        actual = parser(parse_me_full_docstring, "first 2 --three 3".split())
        expected = parse_me_full_docstring("first", 2, 3)
        self.assertEqual(actual, expected)

    def test_function_default(self):
        parser = FunctionParser()
        actual = parser(parse_me_full_docstring, "first 2".split())
        expected = parse_me_full_docstring("first", 2)
        self.assertEqual(actual, expected)


class TestMethodParser(unittest.TestCase):
    def test_create_parser_on_function(self):
        parser = i_am_parseable.parser
        self.assertEqual(parser.description, "I too want to be parseable.")
        self.assertEqual(parser.call(args="yes 2 --three 3".split()), ("yesyes", 9))

    def test_create_parser_on_method(self):
        parser = Dummy.multiply_all.parser
        self.assertEqual(parser.description, "Will multiply everything!")
        self.assertEqual(parser.call(Dummy(12), ["2"]), 48)

    def test_create_parser_on_classmethod(self):
        parser = Dummy.mult.parser
        self.assertEqual(parser.call(Dummy, "2 --e 2".split()), 4)

    def test_create_parser_on_init(self):
        parser = NeedParseClassDecorator.__init__.parser
        self.assertRaises(ParseThisException, parser.call, None, ["2"])

    def test_create_parser_rename(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.could_you_parse_me.parser
        # at this stage the '_' aren't replaced yet
        self.assertEqual(parser.get_name(), "could_you_parse_me")

    def test_create_parser_default_name(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.rename_me_please.parser
        self.assertEqual(parser.get_name(), "new-name")


class TestClassParser(unittest.TestCase):
    def test_parse_class_description(self):
        self.assertEqual(NeedParsing.parser.description, "Hello World")
        self.assertEqual(
            ShowMyDocstring.parser.description, "This should be the parser description"
        )

    def test_parse_class_add_parser(self):
        self.assertTrue(hasattr(NeedParsing, "parser"))
        self.assertTrue(hasattr(NeedParsing(12), "parser"))
        self.assertTrue(hasattr(ShowMyDocstring, "parser"))

    def test_parse_class_subparsers(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 multiply-self-arg 2".split()), 24)
        self.assertEqual(
            parser.call("12 could-you-parse-me yes 2 --three 4".split()), ("yesyes", 16)
        )

    def test_parse_class_expose_private_method(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 private-method 2".split()), 24)

    def test_parse_class_expose_special_method(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 str".split()), "12")

    def test_parse_class_do_not_expose_private_methods(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                ShowMyDocstring.parser.parse_args("will-not-appear 12".split())
            with self.assertRaises(SystemExit):
                ShowMyDocstring.parser.parse_args("str".split())

    def test_parse_class_method_is_still_parseable(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.could_you_parse_me.parser
        self.assertEqual(
            parser.call(need_parsing, "yes 2 --three 3".split()), ("yesyes", 9)
        )

    def test_parse_class_init_need_decoration(self):
        with self.assertRaises(ParseThisException):
            NeedInitDecorator.parser.call("do-stuff 12".split())

    def test_parse_class_need_init_decorator_with_instance(self):
        instance = NeedInitDecorator(2)
        self.assertEqual(
            NeedInitDecorator.parser.call("do-stuff 12".split(), instance), 12
        )
        self.assertEqual(
            NeedInitDecorator.parser.call("do-stuff 12 --div 3".split(), instance), 8
        )

    def test_parse_class_classmethod_is_sub_command(self):
        # A classmethod decorated with @create_parser inside a @parse_class
        # is exposed as a subcommand. The classmethod's cls is bound at
        # descriptor resolution time, not from the __init__'d instance, so
        # it runs exactly as if called through the class itself.
        result = NeedParsing.parser.call("12 parse-me-if-you-can one 2".split())
        self.assertEqual(result, ("oneone", 144))

    def test_parse_class_classmethod_with_cls_access(self):
        # The classmethod can access cls — verify we get the real class,
        # not a surrogate.
        result = ClassAndStaticMethods.parser.call("5 cls-name-upper !".split())
        self.assertEqual(result, "CLASSANDSTATICMETHODS!")

    def test_parse_class_staticmethod_is_sub_command(self):
        result = ClassAndStaticMethods.parser.call("5 static-add 3 4".split())
        self.assertEqual(result, 7)

    def test_parse_class_instance_method_still_works(self):
        # Make sure that adding classmethod/staticmethod support didn't
        # break instance methods in the same class.
        result = ClassAndStaticMethods.parser.call("5 times 6".split())
        self.assertEqual(result, 30)

    def test_parse_class_no_init_classmethod_dispatch(self):
        # A class with no decorated __init__ can still dispatch its
        # classmethods because classmethods don't need an instance — the
        # class object itself is used for dispatch.
        result = OnlyClassMethods.parser.call("described hello".split())
        self.assertEqual(result, "hello: OnlyClassMethods")

    def test_parse_class_no_init_staticmethod_dispatch(self):
        result = OnlyClassMethods.parser.call("square 9".split())
        self.assertEqual(result, 81)

    def test_subcommand_parse_error_shows_subcommand_usage_not_top_parser(self):
        """Regression guard: a parse error caused by an unrecognized argument
        passed to a subcommand must show the subcommand's own usage line, not
        the top-level parser's usage (which lists all available subcommands)."""
        with captured_output() as (_, err):
            with self.assertRaises(SystemExit):
                SubCmdParseError.parser.call("1 sub-cmd 2 --unknown-flag".split())
            error_output = err.getvalue()
        # The subcommand name must appear in the error output as a plain word,
        # confirming the subcommand's usage line was printed.
        self.assertIn("sub-cmd", error_output)
        # The top-level usage line lists subcommands inside braces like
        # "{sub-cmd}" — that must NOT appear, confirming the top-level parser
        # did not report the error.
        self.assertNotIn("{sub-cmd}", error_output)

    def test_parse_class_unrecognized_argument(self):
        with captured_output() as (_, err):
            with self.assertRaises(SystemExit):
                ParseMyInitOnly.parser.call("--unknown-flag".split())
            error_output = err.getvalue()
        self.assertIn("unrecognized arguments", error_output)
        self.assertIn("--unknown-flag", error_output)
        self.assertNotIn("{sub-cmd}", error_output)


def _passthrough_decorator(func):
    """A decorator that wraps func in a *args/**kwargs wrapper via
    functools.wraps — the classic pattern that used to break @create_parser
    stacking because getfullargspec did not follow __wrapped__."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


class TestDecoratorStacking(unittest.TestCase):
    """@create_parser should recover the real signature when stacked on top of
    a decorator that wraps the function in a *args/**kwargs wrapper via
    functools.wraps. The fix uses inspect.unwrap before getfullargspec so
    __wrapped__ is followed to the original callable."""

    def test_create_parser_on_top_of_wraps_based_decorator(self):
        @create_parser()
        @_passthrough_decorator
        def add(a: int, b: int = 3):
            """Add two integers.

            Args:
                a: first number
                b: second number
            """
            return a + b

        # Before the fix, getfullargspec(wrapper) would report no parameters
        # and the parser would be empty. With inspect.unwrap, the real
        # signature is recovered and these calls succeed.
        self.assertEqual(add.parser.call(args=["2"]), 5)
        self.assertEqual(add.parser.call(args=["2", "--b", "4"]), 6)
        # The stacked decorator still wraps the callable.
        self.assertEqual(add(10, 20), 30)

    def test_function_parser_on_top_of_wraps_based_decorator(self):
        """FunctionParser (parse_this as a function) must also follow
        __wrapped__ when the passed function is itself wrapped."""

        @_passthrough_decorator
        def multiply(a: int, b: int = 2):
            """Multiply two integers.

            Args:
                a: first
                b: second
            """
            return a * b

        parser = FunctionParser()
        self.assertEqual(parser(multiply, ["3"]), 6)
        self.assertEqual(parser(multiply, ["3", "--b", "5"]), 15)

    def test_method_on_top_of_wraps_based_decorator_inside_parse_class(self):
        @parse_class()
        class Calculator(object):
            """A calculator."""

            @create_parser()
            def __init__(self, base: int):
                """Init.

                Args:
                    base: starting value
                """
                self._base = base

            @create_parser()
            @_passthrough_decorator
            def add(self, value: int):
                """Add value to base.

                Args:
                    value: amount to add
                """
                return self._base + value

        self.assertEqual(Calculator.parser.call("10 add 5".split()), 15)


class TestLogLevel(unittest.TestCase):
    @patch("parse_this.call.logging.basicConfig")
    def test_function_parser_log_level(self, mock_basic_config):
        parser = FunctionParser()
        result = parser(
            parse_me_full_docstring,
            "first 2 --log-level DEBUG".split(),
            log_level=True,
        )
        self.assertEqual(result, parse_me_full_docstring("first", 2))
        mock_basic_config.assert_called_with(level="DEBUG")

    @patch("parse_this.call.logging.basicConfig")
    def test_create_parser_with_log_level(self, mock_basic_config):
        result = function_with_log_level.parser.call(
            args="yes 2 --log-level WARNING".split()
        )
        self.assertEqual(result, "yesyes")
        mock_basic_config.assert_called_with(level="WARNING")

    @patch("parse_this.call.logging.basicConfig")
    def test_parse_class_with_log_level(self, mock_basic_config):
        result = ParseableWithLogLevel.parser.call(
            "12 --log-level ERROR parseable 2".split()
        )
        self.assertEqual(result, 24)
        mock_basic_config.assert_called_with(level="ERROR")


if __name__ == "__main__":
    unittest.main()
