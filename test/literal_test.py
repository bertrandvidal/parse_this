import unittest
from typing import Literal

from parse_this import create_parser, parse_this
from parse_this.exception import ParseThisException
from test.utils import captured_output


@create_parser()
def has_literal_str(mode: Literal["fast", "slow"]):
    """Pick a mode.

    Args:
        mode: the speed mode
    """
    return mode


@create_parser()
def has_literal_int(count: Literal[1, 2, 3]):
    """Pick a count.

    Args:
        count: how many
    """
    return count


@create_parser()
def has_optional_literal(name: str, mode: Literal["a", "b", "c"] = "a"):
    """Do something.

    Args:
        name: a name
        mode: optional mode
    """
    return name, mode


@create_parser()
def has_mixed_args(name: str, level: Literal[1, 2, 3], verbose: bool = False):
    """Mixed args.

    Args:
        name: a name
        level: the level
        verbose: be verbose
    """
    return name, level, verbose


class TestLiteralRequired(unittest.TestCase):
    def test_literal_str_valid(self):
        self.assertEqual(has_literal_str.parser.call(args=["fast"]), "fast")
        self.assertEqual(has_literal_str.parser.call(args=["slow"]), "slow")

    def test_literal_str_invalid(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                has_literal_str.parser.call(args=["medium"])

    def test_literal_int_valid(self):
        self.assertEqual(has_literal_int.parser.call(args=["2"]), 2)

    def test_literal_int_invalid(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                has_literal_int.parser.call(args=["5"])

    def test_literal_int_preserves_type(self):
        result = has_literal_int.parser.call(args=["1"])
        self.assertIsInstance(result, int)


class TestLiteralOptional(unittest.TestCase):
    def test_optional_literal_default(self):
        self.assertEqual(
            has_optional_literal.parser.call(args=["hello"]), ("hello", "a")
        )

    def test_optional_literal_provided(self):
        self.assertEqual(
            has_optional_literal.parser.call(args=["hello", "--mode", "b"]),
            ("hello", "b"),
        )

    def test_optional_literal_invalid(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                has_optional_literal.parser.call(args=["hello", "--mode", "z"])


class TestLiteralMixedArgs(unittest.TestCase):
    def test_mixed_args(self):
        self.assertEqual(
            has_mixed_args.parser.call(args=["foo", "2"]), ("foo", 2, False)
        )

    def test_mixed_args_with_flag(self):
        self.assertEqual(
            has_mixed_args.parser.call(args=["foo", "1", "--verbose"]),
            ("foo", 1, True),
        )


class TestLiteralFunctionParser(unittest.TestCase):
    def test_function_parser_literal(self):
        def pick(mode: Literal["x", "y"]):
            """Pick.

            Args:
                mode: the mode
            """
            return mode

        result = parse_this(pick, args=["x"])
        self.assertEqual(result, "x")


class TestLiteralErrors(unittest.TestCase):
    def test_mixed_types_raises(self):
        with self.assertRaises(ParseThisException):

            @create_parser()
            def bad_literal(val: Literal[1, "two"]):
                return val

    def test_invalid_default_raises(self):
        with self.assertRaises(ParseThisException):

            @create_parser()
            def bad_default(val: Literal["a", "b"] = "c"):  # type: ignore[assignment]
                return val
