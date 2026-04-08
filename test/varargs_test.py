import unittest

from parse_this import create_parser, parse_class
from parse_this.exception import ParseThisException
from parse_this.parsers import FunctionParser


class TestVarargsSupport(unittest.TestCase):
    def test_varargs_with_annotation_and_values(self):
        @create_parser()
        def total(*nums: int):
            """Sum integers.

            Args:
                nums: integers to sum
            """
            return sum(nums)

        self.assertEqual(total.parser.call(args=["1", "2", "3"]), 6)

    def test_varargs_with_annotation_no_values(self):
        @create_parser()
        def total(*nums: int):
            """Sum integers.

            Args:
                nums: integers to sum
            """
            return sum(nums)

        self.assertEqual(total.parser.call(args=[]), 0)

    def test_varargs_without_annotation_defaults_to_str(self):
        @create_parser()
        def join(*parts):
            """Join the parts.

            Args:
                parts: string parts
            """
            return "-".join(parts)

        self.assertEqual(join.parser.call(args=["a", "b", "c"]), "a-b-c")

    def test_varargs_with_required_positional(self):
        @create_parser()
        def scale(factor: int, *nums: int):
            """Scale a list of numbers.

            Args:
                factor: multiplier
                nums: numbers to scale
            """
            return [factor * n for n in nums]

        self.assertEqual(scale.parser.call(args=["3", "1", "2", "4"]), [3, 6, 12])

    def test_varargs_with_required_and_optional_flag(self):
        # The optional flag has to appear before *values in the signature:
        # keyword-only parameters (anything after *args) are not currently
        # exposed to the parser.
        @create_parser()
        def describe(label: str, verbose: bool = False, *values: int):
            """Label values.

            Args:
                label: text label
                verbose: verbose output
                values: values to describe
            """
            if verbose:
                return f"{label} (verbose): {list(values)}"
            return f"{label}: {list(values)}"

        self.assertEqual(
            describe.parser.call(args=["nums", "1", "2"]),
            "nums: [1, 2]",
        )
        self.assertEqual(
            describe.parser.call(args=["nums", "1", "2", "--verbose"]),
            "nums (verbose): [1, 2]",
        )

    def test_varargs_in_parse_class(self):
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
            def add_all(self, *nums: int):
                """Add all numbers to base.

                Args:
                    nums: values to add
                """
                return self._base + sum(nums)

        self.assertEqual(Calculator.parser.call("10 add-all 1 2 3".split()), 16)
        self.assertEqual(Calculator.parser.call("10 add-all".split()), 10)

    def test_function_parser_direct_call_with_varargs(self):
        def total(*nums: int):
            """Sum integers.

            Args:
                nums: values to sum
            """
            return sum(nums)

        parser = FunctionParser()
        self.assertEqual(parser(total, ["1", "2", "3"]), 6)


class TestKwargsRejection(unittest.TestCase):
    def test_kwargs_rejected_at_decoration_time(self):
        with self.assertRaises(ParseThisException) as ctx:

            @create_parser()
            def f(**opts):
                return opts

        msg = str(ctx.exception)
        self.assertIn("**opts", msg)
        self.assertIn("'f'", msg)

    def test_varargs_and_kwargs_fails_on_kwargs(self):
        with self.assertRaises(ParseThisException) as ctx:

            @create_parser()
            def f(*args, **opts):
                return args, opts

        msg = str(ctx.exception)
        self.assertIn("**opts", msg)

    def test_kwargs_in_function_parser_direct_call(self):
        def f(**opts):
            return opts

        parser = FunctionParser()
        with self.assertRaises(ParseThisException):
            parser(f, [])

    def test_kwargs_in_method_parser_on_class(self):
        with self.assertRaises(ParseThisException):

            class C(object):
                @create_parser()
                def method(self, **opts):
                    return opts


if __name__ == "__main__":
    unittest.main()
