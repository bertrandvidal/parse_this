import unittest

from parse_this import create_parser, parse_class
from parse_this.exception import ParseThisException
from parse_this.parsing import (
    _get_arg_parser,
    _get_parseable_methods,
)
from parse_this.types import _check_types
from parse_this.values import _NO_DEFAULT
from test.utils import captured_output


def no_docstring():
    pass


def with_args(a, b):
    pass


@parse_class()
class Parseable(object):
    @create_parser()
    def __init__(self, a: int):
        self._a = a

    @create_parser()
    def _private_method(self, b: int):
        return self._a * b

    def not_parseable(self, c: int):
        return self._a * c

    @create_parser()
    def parseable(self, d: int):
        return self._a * d

    @classmethod
    @create_parser()
    def cls_method(cls, e: int):
        return e * e


@parse_class(parse_private=True)
class ParseableWithPrivateMethod(object):
    @create_parser()
    def __init__(self, a: int):
        self._a = a

    @create_parser()
    def _private_method(self, b: int):
        return self._a * b

    def not_parseable(self, c: int):
        return self._a * c

    @create_parser()
    def parseable(self, d: int):
        return self._a * d

    @classmethod
    @create_parser()
    def cls_method(cls, e: int):
        return e * e


def blank_line_in_wrong_place(one: int, two: int):
    """I put the blank line after arguments ...

    Args:
        one: this help is #1

        two: this once won't appear sadly
    """
    return one * two


def parse_me_full_docstring(one: str, two: int, three: int = 12):
    """Could use some parsing.

    Args:
        one: some stuff shouldn't be written down
        two: I can turn 2 syllables words into 6 syllables words
        three: I don't like the number three

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


def parse_me_no_docstring(one: int, two: int, three: int):
    return one * two, three * three


def multiline_docstring(one: int, two: int, three: int):
    """I am a sneaky function.

    Args:
        one: this one is a no brainer
        three: noticed you're missing docstring for two and
          I'm multiline too!

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


def different_delimiter_chars(one: int, two: int, three: int):
    """I am a sneaky function.

    Args:
        one -- this one is a no brainer even with dashes
        three -- noticed you're missing docstring for two and
          I'm multiline too!

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


@create_parser()
def concatenate_string(string: str, nb_concat: int):
    return string * nb_concat


@create_parser()
def has_none_default_value(a: int, b: str = None):
    return a, b


@create_parser()
def has_flags(a: int, b: bool = False):
    return a, b


@create_parser()
def has_bool_arguments(a: bool):
    return a


class TestCore(unittest.TestCase):
    def test_get_parseable_methods(self):
        (init_parser, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertIsNotNone(init_parser)
        self.assertListEqual(
            sorted(list(method_to_parser.keys())), ["_private_method", "parseable"]
        )

    def test_get_parseable_methods_do_not_include_classmethod(self):
        (_, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertNotIn("cls_method", method_to_parser.keys())

    def test_get_arg_parser_bool_argument(self):
        self.assertEqual(has_bool_arguments.parser.call(args=[]), True)
        self.assertEqual(has_bool_arguments.parser.call(args=["--a"]), False)

    def test_get_arg_parser_bool_default_value(self):
        self.assertEqual(has_flags.parser.call(args=["12"]), (12, False))
        self.assertEqual(has_flags.parser.call(args=["12", "--b"]), (12, True))

    def test_get_arg_parser_none_default_value_without_type(self):
        with self.assertRaises(ParseThisException):

            @create_parser(int)
            def have_none_default_value(a: int, b=None):
                pass

    def test_get_arg_parser_with_none_default_value(self):
        self.assertEqual(has_none_default_value.parser.call(args=["12"]), (12, None))
        self.assertEqual(
            has_none_default_value.parser.call(args=["12", "--b", "yes"]), (12, "yes")
        )

    def test_get_arg_parser_annotation_take_precedence(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": int, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", _NO_DEFAULT)],
            ":",
        )
        namespace = parser.parse_args("1 2 3".split())
        self.assertEqual(namespace.one, 1)
        self.assertEqual(namespace.two, 2)
        self.assertEqual(namespace.three, 3)

    def test_get_arg_parser_with_default_value(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        namespace = parser.parse_args("yes 42".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 42)
        self.assertEqual(namespace.three, 12)

    def test_get_arg_parser_without_default_value(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        namespace = parser.parse_args("no 12 --three=23".split())
        self.assertEqual(namespace.one, "no")
        self.assertEqual(namespace.two, 12)
        self.assertEqual(namespace.three, 23)

    def test_get_arg_parser_required_arguments(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        with captured_output():
            self.assertRaises(
                SystemExit, parser.parse_args, "we_are_missing_two".split()
            )

    def test_get_arg_parser_argument_type(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        with captured_output():
            self.assertRaises(
                SystemExit, parser.parse_args, "yes i_should_be_an_int".split()
            )

    def test_check_types_not_enough_types_provided(self):
        self.assertRaises(
            ParseThisException, _check_types, "function", {}, ["i_dont_have_a_type"], ()
        )

    def test_check_types_too_many_types_provided(self):
        self.assertRaises(
            ParseThisException,
            _check_types,
            "function",
            {"a": int, "b": int},
            ["i_am_alone"],
            (),
        )

    def test_check_types_with_default(self):
        func_args = ["i_am_alone", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int, "i_have_a_default_value": str},
                func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_with_default_type_not_specified(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function", {"i_am_an_int": int}, func_args, ("default_value",)
            ),
            func_args,
        )

    def test_check_types_remove_self(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int},
                ["self"] + func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_remove_class(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int},
                ["cls"] + func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_no_args(self):
        self.assertEqual(_check_types("function", {}, [], ()), [])

    def test_check_types_return_annotation(self):
        self.assertEqual(_check_types("function", {"return": int}, [], ()), [])


class TestFullHelpAction(unittest.TestCase):
    def test_help_is_complete(self):
        with captured_output() as (out, _):
            self.assertRaises(SystemExit, Parseable.parser.parse_args, ["-h"])
            help_message = out.getvalue()
        self.assertIn("parseable", help_message)
        # Private methods and classmethods are not exposed by default
        self.assertNotIn("private_method", help_message)
        self.assertNotIn("cls_method", help_message)

    def test_help_is_complete_with_private_method(self):
        with captured_output() as (out, _):
            self.assertRaises(
                SystemExit, ParseableWithPrivateMethod.parser.parse_args, ["-h"]
            )
            help_message = out.getvalue()
        self.assertIn("parseable", help_message)
        self.assertIn("private_method", help_message)
        # Classmethods are not exposed by default
        self.assertNotIn("cls_method", help_message)


if __name__ == "__main__":
    unittest.main()
