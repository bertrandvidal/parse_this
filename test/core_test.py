from parse_this import create_parser
from parse_this.core import (_get_args_and_defaults, NoDefault,
                             _get_default_help_message, Self,
                             _get_parseable_methods, Class, _prepare_doc,
                             _get_arg_parser)
import unittest


def no_docstring():
    pass


def with_args(a, b):
    pass


class Parsable(object):

    @create_parser(Self, int)
    def __init__(self, a):
        self._a = a

    @create_parser(Self, int)
    def _private_method(self, b):
        return self._a * b

    def not_parseable(self, c):
        return self._a * c

    @create_parser(Self, int)
    def parseable(self, d):
        return self._a * d

    @classmethod
    @create_parser(Class, int)
    def cls_method(cls, e):
        return e * e


def blank_line_in_wrong_place(one, two):
    """I put the blank line after arguments ...

    Args:
        one: this help is #1

        two: this once won't appear sadly
    """
    return one * two


def parse_me_full_docstring(one, two, three=12):
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


def parse_me_no_docstring(one, two, three):
    return one * two, three * three


def multiline_docstring(one, two, three):
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


def different_params_delimiter(one, two, three):
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


class TestCore(unittest.TestCase):

    def test_get_args_and_defaults_fill_no_default(self):
        args_and_defaults = _get_args_and_defaults(["first", "second", "third"],
                                                   ("default_value",))
        self.assertListEqual(args_and_defaults, [("first", NoDefault),
                                                 ("second", NoDefault),
                                                 ("third", "default_value")])

    def test_get_args_and_defaults_no_args(self):
        self.assertListEqual(_get_args_and_defaults([], ()), [])

    def test_get_args_and_defaults_no_default(self):
        self.assertListEqual(_get_args_and_defaults(["first", "second"], ()),
                             [("first", NoDefault), ("second", NoDefault)])

    def test_get_default_help_message_no_docstring(self):
        (description, _) = _get_default_help_message(no_docstring, [])
        self.assertIsNotNone(description)
        self.assertIn(no_docstring.__name__, description)

    def test_get_default_help_message_add_default_args_help(self):
        (_, args_help) = _get_default_help_message(with_args, ["a", "b"])
        self.assertListEqual(args_help.keys(), ["a", "b"])
        (_, args_help) = _get_default_help_message(with_args, ["a", "b"], None,
                                                   {"a": "I have an help message"})
        self.assertListEqual(args_help.keys(), ["a", "b"])

    def test_get_parseable_methods(self):
        (init_parser, method_to_parser) = _get_parseable_methods(Parsable)
        self.assertIsNotNone(init_parser)
        self.assertListEqual(method_to_parser.keys(), ["parseable",
                                                       "_private_method"])

    def test_get_parseable_methods_do_not_include_classmethod(self):
        (_, method_to_parser) = _get_parseable_methods(Parsable)
        self.assertNotIn("cls_method", method_to_parser.keys())

    def test_prepare_doc_blank_line_in_wrong_place(self):
        (description, help_msg) = _prepare_doc(blank_line_in_wrong_place,
                                               ["one", "two"], ":")
        self.assertEqual(description, "I put the blank line after arguments ...")
        self.assertEqual(help_msg, {"one": "this help is #1",
                                    "two": "Help message for two"})

    def test_prepare_doc_full_docstring(self):
        (description, help_msg) = _prepare_doc(parse_me_full_docstring,
                                               ["one", "two", "three"], ":")
        self.assertEqual(description, "Could use some parsing.")
        self.assertEqual(help_msg, {"one":"some stuff shouldn't be written down",
                                    "two":"I can turn 2 syllables words into 6 syllables words",
                                    "three": "I don't like the number three"})

    def test_prepare_doc_no_docstring(self):
        (description, help_msg) = _prepare_doc(parse_me_no_docstring,
                                               ["one", "two", "three"], ":")
        self.assertEqual(description, "Argument parsing for parse_me_no_docstring")
        self.assertEqual(help_msg, {"one": "Help message for one",
                                    "two":  "Help message for two",
                                    "three":  "Help message for three"})

    def test_prepare_doc_will_you_dare(self):
        (description, help_msg) = _prepare_doc(multiline_docstring,
                                               ["one", "two", "three"], ":")
        self.assertEqual(description, "I am a sneaky function.")
        self.assertEqual(help_msg, {"one": "this one is a no brainer",
                                    "two": "Help message for two",
                                    "three": "noticed you're missing docstring for two and I'm multiline too!"})

    def test_prepare_doc_params_delim(self):
        (description, help_msg) = _prepare_doc(different_params_delimiter,
                                               ["one", "two", "three"], "--")
        self.assertEqual(description, "I am a sneaky function.")
        self.assertEqual(help_msg, {"one": "this one is a no brainer even with dashes",
                                    "two": "Help message for two",
                                    "three": "noticed you're missing docstring for two and I'm multiline too!"})

    def test_get_arg_parser_with_default_value(self):
        parser = _get_arg_parser(parse_me_full_docstring,
                                 [str, int], [("one", NoDefault),
                                              ("two", NoDefault),
                                              ("three", 12)], ":")
        namespace = parser.parse_args("yes 42".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 42)
        self.assertEqual(namespace.three, 12)

    def test_get_arg_parser_without_default_value(self):
        parser = _get_arg_parser(parse_me_full_docstring, [str, int],
                                 [("one", NoDefault), ("two", NoDefault),
                                  ("three", 12)], ":")
        namespace = parser.parse_args("no 12 --three=23".split())
        self.assertEqual(namespace.one, "no")
        self.assertEqual(namespace.two, 12)
        self.assertEqual(namespace.three, 23)

    def test_get_arg_parser_required_arguments(self):
        parser = _get_arg_parser(parse_me_full_docstring, [str, int],
                                 [("one", NoDefault), ("two", NoDefault),
                                  ("three", 12)], ":")
        self.assertRaises(SystemExit, parser.parse_args,
                          "we_are_missing_two".split())

    def test_get_arg_parser_argument_type(self):
        parser = _get_arg_parser(parse_me_full_docstring, [str, int],
                                 [("one", NoDefault), ("two", NoDefault),
                                  ("three", 12)], ":")
        self.assertRaises(SystemExit, parser.parse_args,
                          "yes i_should_be_an_int".split())


if __name__ == "__main__":
    unittest.main()
