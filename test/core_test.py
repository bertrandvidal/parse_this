import unittest

from parse_this import create_parser
from parse_this.exception import ParseThisException
from test.helpers import Parseable, ParseableWithPrivateMethod
from test.utils import captured_output


def no_docstring():
    pass


def with_args(a, b):
    pass


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


# TODO(bvidal): move to help_test file
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
