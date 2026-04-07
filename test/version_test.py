import unittest

from parse_this import create_parser, parse_class, parse_this
from test.utils import captured_output


def add(a: int, b: int):
    """Add two numbers.

    Args:
        a: first number
        b: second number
    """
    return a + b


@parse_class(version="myapp 2.0.1")
class VersionedApp(object):
    """An app with a version."""

    @create_parser()
    def __init__(self, multiplier: int):
        """Init.

        Args:
            multiplier: a value
        """
        self._mult = multiplier

    @create_parser()
    def run(self, value: int):
        """Run something.

        Args:
            value: input value
        """
        return self._mult * value


@parse_class()
class UnversionedApp(object):
    """An app without a version."""

    @create_parser()
    def __init__(self, multiplier: int):
        """Init.

        Args:
            multiplier: a value
        """
        self._mult = multiplier

    @create_parser()
    def run(self, value: int):
        """Run something.

        Args:
            value: input value
        """
        return self._mult * value


class TestFunctionParserVersion(unittest.TestCase):
    def test_version_flag_prints_and_exits(self):
        with captured_output() as (out, err):
            with self.assertRaises(SystemExit) as ctx:
                parse_this(add, args=["--version"], version="add 1.2.3")
        self.assertEqual(ctx.exception.code, 0)
        # argparse < 3.4 prints to stderr; >= 3.4 prints to stdout
        printed = out.getvalue() + err.getvalue()
        self.assertIn("add 1.2.3", printed)

    def test_version_in_help(self):
        with captured_output() as (out, _):
            with self.assertRaises(SystemExit):
                parse_this(add, args=["--help"], version="add 1.2.3")
        self.assertIn("--version", out.getvalue())

    def test_no_version_flag_when_omitted(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                parse_this(add, args=["--version"])

    def test_prog_substitution(self):
        with captured_output() as (out, err):
            with self.assertRaises(SystemExit):
                parse_this(add, args=["--version"], version="%(prog)s 9.9.9")
        printed = out.getvalue() + err.getvalue()
        # argparse derives prog from sys.argv[0]; under pytest this is the
        # pytest entrypoint. We just need to verify substitution happened
        # (i.e. the literal "%(prog)s" was replaced) and the version is
        # present.
        self.assertNotIn("%(prog)s", printed)
        self.assertIn("9.9.9", printed)
        # The prog name precedes the version string in argparse's output.
        self.assertRegex(printed, r"\S+ 9\.9\.9")


class TestClassParserVersion(unittest.TestCase):
    def test_version_flag_prints_and_exits(self):
        with captured_output() as (out, err):
            with self.assertRaises(SystemExit) as ctx:
                VersionedApp.parser.call(args=["--version"])
        self.assertEqual(ctx.exception.code, 0)
        printed = out.getvalue() + err.getvalue()
        self.assertIn("myapp 2.0.1", printed)

    def test_version_in_help(self):
        with captured_output() as (out, _):
            with self.assertRaises(SystemExit):
                VersionedApp.parser.call(args=["--help"])
        self.assertIn("--version", out.getvalue())

    def test_no_version_flag_when_omitted(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                UnversionedApp.parser.call(args=["--version"])

    def test_call_without_version_still_works(self):
        self.assertEqual(VersionedApp.parser.call(args=["3", "run", "4"]), 12)
