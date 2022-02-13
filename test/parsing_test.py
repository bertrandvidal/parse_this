import unittest

from parse_this import create_parser
from parse_this.args import _NO_DEFAULT
from parse_this.exception import ParseThisException
from parse_this.parsing import _get_arg_parser, _get_parseable_methods
from test.helpers import (
    Parseable,
    has_bool_arguments,
    has_flags,
    has_none_default_value,
    parse_me_full_docstring,
)
from test.utils import captured_output


class TestParsing(unittest.TestCase):
    def test_get_arg_parser_bool_argument(self):
        self.assertEqual(has_bool_arguments.parser.call(args=[]), True)
        self.assertEqual(has_bool_arguments.parser.call(args=["--a"]), False)

    def test_get_arg_parser_bool_default_value(self):
        self.assertEqual(has_flags.parser.call(args=["12"]), (12, False))
        self.assertEqual(has_flags.parser.call(args=["12", "--b"]), (12, True))

    def test_get_arg_parser_with_none_default_value(self):
        self.assertEqual(has_none_default_value.parser.call(args=["12"]), (12, None))
        self.assertEqual(
            has_none_default_value.parser.call(args=["12", "--b", "yes"]), (12, "yes")
        )

    def test_get_arg_parser_none_default_value_without_type(self):
        with self.assertRaises(ParseThisException):

            @create_parser(int)
            def have_none_default_value(a: int, b=None):
                pass

    def test_get_parseable_methods(self):
        (init_parser, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertIsNotNone(init_parser)
        self.assertListEqual(
            sorted(list(method_to_parser.keys())), ["_private_method", "parseable"]
        )

    def test_get_parseable_methods_do_not_include_classmethod(self):
        (_, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertNotIn("cls_method", method_to_parser.keys())

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


if __name__ == "__main__":
    unittest.main()
