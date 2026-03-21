import unittest
from argparse import ArgumentParser

from parse_this import create_parser
from parse_this.args import _NO_DEFAULT
from parse_this.exception import ParseThisException
from parse_this.parsing import (
    _add_log_level_argument,
    _get_arg_parser,
    _get_args_name_from_parser,
    _get_parseable_methods,
)
from test.helpers import (
    Color,
    Parseable,
    has_bool_arguments,
    has_enum_argument,
    has_enum_default,
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
        init_parser, method_to_parser = _get_parseable_methods(Parseable)
        self.assertIsNotNone(init_parser)
        self.assertListEqual(
            sorted(list(method_to_parser.keys())), ["_private_method", "parseable"]
        )

    def test_get_parseable_methods_do_not_include_classmethod(self):
        _, method_to_parser = _get_parseable_methods(Parseable)
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

    def test_add_log_level_argument(self):
        parser = ArgumentParser()
        _add_log_level_argument(parser)
        namespace = parser.parse_args("--log-level DEBUG".split())
        self.assertEqual(namespace.log_level, "DEBUG")

    def test_add_log_level_argument_not_required(self):
        parser = ArgumentParser()
        _add_log_level_argument(parser)
        namespace = parser.parse_args([])
        self.assertIsNone(namespace.log_level)

    def test_add_log_level_argument_invalid(self):
        parser = ArgumentParser()
        _add_log_level_argument(parser)
        with captured_output():
            with self.assertRaises(SystemExit):
                parser.parse_args("--log-level INVALID".split())

    def test_get_args_name_from_parser(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        args = _get_args_name_from_parser(parser)
        self.assertEqual(args, ["one", "two", "three"])

    def test_get_args_name_from_parser_excludes_help(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
        )
        args = _get_args_name_from_parser(parser)
        self.assertNotIn("help", args)

    def test_get_args_name_from_parser_excludes_log_level(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            {"one": str, "two": int, "three": int},
            [("one", _NO_DEFAULT), ("two", _NO_DEFAULT), ("three", 12)],
            ":",
            log_level=True,
        )
        args = _get_args_name_from_parser(parser)
        self.assertNotIn("log_level", args)

    def test_get_arg_parser_enum_positional_argument(self):
        self.assertEqual(has_enum_argument.parser.call(args=["RED"]), Color.RED)

    def test_get_arg_parser_enum_positional_invalid(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                has_enum_argument.parser.call(args=["PURPLE"])

    def test_get_arg_parser_enum_default_value(self):
        self.assertEqual(has_enum_default.parser.call(args=["1"]), (1, Color.RED))

    def test_get_arg_parser_enum_override_default(self):
        self.assertEqual(
            has_enum_default.parser.call(args=["1", "--color", "GREEN"]),
            (1, Color.GREEN),
        )

    def test_get_arg_parser_enum_choices_registered(self):
        parser = _get_arg_parser(
            has_enum_argument,
            {"color": Color},
            [("color", _NO_DEFAULT)],
            ":",
        )
        # Find the action for 'color' and check its choices contain all members
        color_action = next(
            action for action in parser._actions if action.dest == "color"
        )
        self.assertEqual(color_action.choices, list(Color))


if __name__ == "__main__":
    unittest.main()
