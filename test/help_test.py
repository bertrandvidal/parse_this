import unittest

from parse_this.help.description import _get_default_help_message, prepare_doc
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


class TestHelp(unittest.TestCase):
    def test_get_default_help_message_no_docstring(self):
        (description, _) = _get_default_help_message(no_docstring, [])
        self.assertIsNotNone(description)
        self.assertIn(no_docstring.__name__, description)

    def test_get_default_help_message_add_default_args_help(self):
        (_, args_help) = _get_default_help_message(with_args, ["a", "b"])
        self.assertListEqual(sorted(list(args_help.keys())), ["a", "b"])
        (_, args_help) = _get_default_help_message(
            with_args, ["a", "b"], None, {"a": "I have an help message"}
        )
        self.assertListEqual(sorted(list(args_help.keys())), ["a", "b"])

    def test_prepare_doc_blank_line_in_wrong_place(self):
        (description, help_msg) = prepare_doc(
            blank_line_in_wrong_place, ["one", "two"], ":"
        )
        self.assertEqual(description, "I put the blank line after arguments ...")
        self.assertEqual(
            help_msg, {"one": "this help is #1", "two": "Help message for two"}
        )

    def test_prepare_doc_full_docstring(self):
        (description, help_msg) = prepare_doc(
            parse_me_full_docstring, ["one", "two", "three"], ":"
        )
        self.assertEqual(description, "Could use some parsing.")
        self.assertEqual(
            help_msg,
            {
                "one": "some stuff shouldn't be written down",
                "two": "I can turn 2 syllables words into 6 syllables words",
                "three": "I don't like the number three",
            },
        )

    def test_prepare_doc_no_docstring(self):
        (description, help_msg) = prepare_doc(
            parse_me_no_docstring, ["one", "two", "three"], ":"
        )
        self.assertEqual(description, "Argument parsing for parse_me_no_docstring")
        self.assertEqual(
            help_msg,
            {
                "one": "Help message for one",
                "two": "Help message for two",
                "three": "Help message for three",
            },
        )

    def test_prepare_doc_will_you_dare(self):
        (description, help_msg) = prepare_doc(
            multiline_docstring, ["one", "two", "three"], ":"
        )
        self.assertEqual(description, "I am a sneaky function.")
        self.assertEqual(
            help_msg,
            {
                "one": "this one is a no brainer",
                "two": "Help message for two",
                "three": "noticed you're missing docstring for two and "
                + "I'm multiline too!",
            },
        )

    def test_prepare_doc_delimiter_chars(self):
        (description, help_msg) = prepare_doc(
            different_delimiter_chars, ["one", "two", "three"], "--"
        )
        self.assertEqual(description, "I am a sneaky function.")
        self.assertEqual(
            help_msg,
            {
                "one": "this one is a no brainer even with dashes",
                "two": "Help message for two",
                "three": "noticed you're missing docstring for two and "
                + "I'm multiline too!",
            },
        )


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
