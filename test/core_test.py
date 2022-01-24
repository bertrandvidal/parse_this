from collections import namedtuple
import unittest

from parse_this import create_parser, parse_class
from test.utils import captured_output
from parse_this.core import (
    _get_args_and_defaults,
    NoDefault,
    _get_default_help_message,
    Self,
    _get_parseable_methods,
    Class,
    _prepare_doc,
    _get_arg_parser,
    _get_args_to_parse,
    ParseThisError,
    _check_types,
    _get_parser_call_method,
    _call,
    _call_method_from_namespace,
    identity_type,
)


def no_docstring():
    pass


def with_args(a, b):
    pass


@parse_class()
class Parseable(object):
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


@parse_class(parse_private=True)
class ParseableWithPrivateMethod(object):
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


def different_delimiter_charsiter(one, two, three):
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


@create_parser(str, int)
def concatenate_string(string, nb_concat):
    return string * nb_concat


@create_parser(int, str)
def has_none_default_value(a, b=None):
    return a, b


@create_parser(int)
def has_flags(a, b=False):
    return a, b


@create_parser(bool)
def has_bool_arguments(a):
    return a


class TestCore(unittest.TestCase):
    def test_identity_type(self):
        self.assertEqual(None, identity_type(None))

    def test_get_args_and_defaults_fill_no_default(self):
        args_and_defaults = _get_args_and_defaults(
            ["first", "second", "third"], ("default_value",)
        )
        self.assertListEqual(
            args_and_defaults,
            [("first", NoDefault), ("second", NoDefault), ("third", "default_value")],
        )

    def test_get_args_and_defaults_no_args(self):
        self.assertListEqual(_get_args_and_defaults([], ()), [])

    def test_get_args_and_defaults_no_default(self):
        self.assertListEqual(
            _get_args_and_defaults(["first", "second"], ()),
            [("first", NoDefault), ("second", NoDefault)],
        )

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

    def test_get_parseable_methods(self):
        (init_parser, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertIsNotNone(init_parser)
        self.assertListEqual(
            sorted(list(method_to_parser.keys())), ["_private_method", "parseable"]
        )

    def test_get_parseable_methods_do_not_include_classmethod(self):
        (_, method_to_parser) = _get_parseable_methods(Parseable)
        self.assertNotIn("cls_method", method_to_parser.keys())

    def test_prepare_doc_blank_line_in_wrong_place(self):
        (description, help_msg) = _prepare_doc(
            blank_line_in_wrong_place, ["one", "two"], ":"
        )
        self.assertEqual(description, "I put the blank line after arguments ...")
        self.assertEqual(
            help_msg, {"one": "this help is #1", "two": "Help message for two"}
        )

    def test_prepare_doc_full_docstring(self):
        (description, help_msg) = _prepare_doc(
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
        (description, help_msg) = _prepare_doc(
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
        (description, help_msg) = _prepare_doc(
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
        (description, help_msg) = _prepare_doc(
            different_delimiter_charsiter, ["one", "two", "three"], "--"
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

    def test_get_arg_parser_bool_argument(self):
        self.assertEqual(has_bool_arguments.parser.call(args=[]), True)
        self.assertEqual(has_bool_arguments.parser.call(args=["--a"]), False)

    def test_get_arg_parser_bool_default_value(self):
        self.assertEqual(has_flags.parser.call(args=["12"]), (12, False))
        self.assertEqual(has_flags.parser.call(args=["12", "--b"]), (12, True))

    def test_get_arg_parser_none_default_value_without_type(self):
        with self.assertRaises(ParseThisError):

            @create_parser(int)
            def have_none_default_value(a, b=None):
                pass

    def test_get_arg_parser_with_none_default_value(self):
        self.assertEqual(has_none_default_value.parser.call(args=["12"]), (12, None))
        self.assertEqual(
            has_none_default_value.parser.call(args=["12", "--b", "yes"]), (12, "yes")
        )

    def test_get_arg_parser_with_default_value(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            [str, int],
            [("one", NoDefault), ("two", NoDefault), ("three", 12)],
            ":",
        )
        namespace = parser.parse_args("yes 42".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 42)
        self.assertEqual(namespace.three, 12)

    def test_get_arg_parser_without_default_value(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            [str, int],
            [("one", NoDefault), ("two", NoDefault), ("three", 12)],
            ":",
        )
        namespace = parser.parse_args("no 12 --three=23".split())
        self.assertEqual(namespace.one, "no")
        self.assertEqual(namespace.two, 12)
        self.assertEqual(namespace.three, 23)

    def test_get_arg_parser_required_arguments(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            [str, int],
            [("one", NoDefault), ("two", NoDefault), ("three", 12)],
            ":",
        )
        with captured_output():
            self.assertRaises(
                SystemExit, parser.parse_args, "we_are_missing_two".split()
            )

    def test_get_arg_parser_argument_type(self):
        parser = _get_arg_parser(
            parse_me_full_docstring,
            [str, int],
            [("one", NoDefault), ("two", NoDefault), ("three", 12)],
            ":",
        )
        with captured_output():
            self.assertRaises(
                SystemExit, parser.parse_args, "yes i_should_be_an_int".split()
            )

    def test_get_args_to_parse_nothing_to_parse(self):
        self.assertListEqual(_get_args_to_parse(None, []), [])

    def test_get_args_to_parse_remove_prog_from_sys_argv(self):
        self.assertListEqual(
            _get_args_to_parse(None, ["prog", "arg_1", "arg_2"]), ["arg_1", "arg_2"]
        )

    def test_get_args_to_parse_with_options(self):
        self.assertListEqual(
            _get_args_to_parse(None, ["prog", "arg", "--kwargs=12"]),
            ["arg", "--kwargs=12"],
        )

    def test_get_args_to_parse_used_empty_args_not_sys_argv(self):
        self.assertListEqual(_get_args_to_parse([], ["prog", "arg_1", "arg_2"]), [])

    def test_check_types_not_enough_types_provided(self):
        self.assertRaises(
            ParseThisError, _check_types, "function", [], ["i_dont_have_a_type"], ()
        )

    def test_check_types_too_many_types_provided(self):
        self.assertRaises(
            ParseThisError, _check_types, "function", [int, str], ["i_am_alone"], ()
        )

    def test_check_types_with_default(self):
        types = [int, str]
        func_args = ["i_am_alone", "i_have_a_default_value"]
        self.assertEqual(
            _check_types("function", types, func_args, ("default_value",)),
            (types, func_args),
        )

    def test_check_types_with_default_type_not_specified(self):
        types = [int]
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types("function", types, func_args, ("default_value",)),
            (types, func_args),
        )

    def test_check_types_remove_self(self):
        types = [int]
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function", [Self] + types, ["self"] + func_args, ("default_value",)
            ),
            ([int], func_args),
        )

    def test_check_types_remove_class(self):
        types = [int]
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function", [Class] + types, ["cls"] + func_args, ("default_value",)
            ),
            ([int], func_args),
        )

    def test_check_types_no_args(self):
        self.assertEqual(_check_types("function", [], [], ()), ([], []))

    def test_get_parser_call_method_returns_callable(self):
        call_method = _get_parser_call_method(concatenate_string)
        self.assertTrue(callable(call_method))

    def test_get_parser_call_method_raise_on_init(self):
        call_method = _get_parser_call_method(Parseable.__init__)
        self.assertRaises(ParseThisError, call_method, None)

    def test_get_parser_call_method_execution(self):
        call_method = _get_parser_call_method(Parseable.parseable)
        self.assertEqual(call_method(Parseable(12), ["2"]), 24)

    def test_get_parser_call_method_on_function(self):
        call_method = _get_parser_call_method(concatenate_string)
        self.assertEqual(call_method(args="yes 2".split()), "yesyes")

    def test_call_on_parse_me_no_docstring(self):
        Namespace = namedtuple("Namespace", ["one", "two", "three"])
        fake_namespace = Namespace(**{"one": 2, "two": 12, "three": 3})
        self.assertEqual(
            _call(parse_me_no_docstring, ["one", "two", "three"], fake_namespace),
            (24, 9),
        )

    def test_call_method_from_namespace_create_instance(self):
        Namespace = namedtuple("Namespace", ["a"])
        fake_namespace = Namespace(a=2)
        parseable = _call_method_from_namespace(Parseable, "__init__", fake_namespace)
        self.assertIsInstance(parseable, Parseable)
        self.assertEqual(parseable._a, 2)

    def test_call_method_from_namespace_execution(self):
        Namespace = namedtuple("Namespace", ["d"])
        fake_namespace = Namespace(d=2)
        self.assertEqual(
            _call_method_from_namespace(Parseable(12), "parseable", fake_namespace), 24
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
