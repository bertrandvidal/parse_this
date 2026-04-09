import unittest
from typing import Optional, Union

from parse_this import create_parser
from parse_this.exception import ParseThisException
from parse_this.helpers import _unwrap_optional


class TestUnwrapOptional(unittest.TestCase):
    def test_unwrap_optional_int(self):
        self.assertIs(_unwrap_optional(Optional[int]), int)

    def test_unwrap_optional_str(self):
        self.assertIs(_unwrap_optional(Optional[str]), str)

    def test_unwrap_union_none(self):
        self.assertIs(_unwrap_optional(Union[int, None]), int)

    def test_unwrap_pep604_int_none(self):
        self.assertIs(_unwrap_optional(int | None), int)

    def test_unwrap_non_union_returns_unchanged(self):
        self.assertIs(_unwrap_optional(int), int)
        self.assertIs(_unwrap_optional(str), str)
        # list[int] creates a new GenericAlias each call, so compare by value.
        self.assertEqual(_unwrap_optional(list[int]), list[int])

    def test_unwrap_union_two_non_none_arms_raises(self):
        with self.assertRaises(ParseThisException) as ctx:
            _unwrap_optional(Union[int, str])
        self.assertIn("multiple non-None arms", str(ctx.exception))

    def test_unwrap_pep604_two_non_none_arms_raises(self):
        with self.assertRaises(ParseThisException):
            _unwrap_optional(int | str)


class TestOptionalArgumentParsing(unittest.TestCase):
    def test_optional_int_with_default_none_omitted(self):
        @create_parser()
        def f(a: int, b: Optional[int] = None):
            return a, b

        self.assertEqual(f.parser.call(args=["5"]), (5, None))

    def test_optional_int_with_default_none_provided(self):
        @create_parser()
        def f(a: int, b: Optional[int] = None):
            return a, b

        self.assertEqual(f.parser.call(args=["5", "--b", "7"]), (5, 7))

    def test_optional_str_with_default_none(self):
        @create_parser()
        def f(a: int, b: Optional[str] = None):
            return a, b

        self.assertEqual(f.parser.call(args=["5"]), (5, None))
        self.assertEqual(f.parser.call(args=["5", "--b", "hello"]), (5, "hello"))

    def test_union_int_none_syntax(self):
        @create_parser()
        def f(a: int, b: Union[int, None] = None):
            return a, b

        self.assertEqual(f.parser.call(args=["5"]), (5, None))
        self.assertEqual(f.parser.call(args=["5", "--b", "42"]), (5, 42))

    def test_pep604_int_none_syntax(self):
        @create_parser()
        def f(a: int, b: int | None = None):
            return a, b

        self.assertEqual(f.parser.call(args=["5"]), (5, None))
        self.assertEqual(f.parser.call(args=["5", "--b", "42"]), (5, 42))

    def test_optional_int_required_positional(self):
        """Optional[int] without a default is treated as a required positional
        int — the Optional wrapper is unwrapped and the argument still has no
        default, so argparse registers it as positional."""

        @create_parser()
        def f(a: Optional[int]):
            return a

        self.assertEqual(f.parser.call(args=["42"]), 42)

    def test_union_with_two_non_none_arms_rejected(self):
        with self.assertRaises(ParseThisException) as ctx:

            @create_parser()
            def f(a: int, b: Union[int, str] = 1):
                return a, b

        self.assertIn("multiple non-None arms", str(ctx.exception))

    def test_none_default_without_annotation_improved_message(self):
        with self.assertRaises(ParseThisException) as ctx:

            @create_parser()
            def f(a: int, b=None):
                return a, b

        msg = str(ctx.exception)
        self.assertIn("'b'", msg)
        self.assertIn("'f'", msg)
        self.assertIn("int | None", msg)


if __name__ == "__main__":
    unittest.main()
