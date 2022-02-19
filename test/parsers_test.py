import unittest

from parse_this.exception import ParseThisException
from parse_this.parsers import FunctionParser
from test.helpers import (
    Dummy,
    NeedInitDecorator,
    NeedParseClassDecorator,
    NeedParsing,
    ShowMyDocstring,
    different_delimiter_chars,
    i_am_parseable,
    parse_me_full_docstring,
)
from test.utils import captured_output


class TestFunctionParser(unittest.TestCase):
    def test_function_return(self):
        parser = FunctionParser()
        actual = parser(parse_me_full_docstring, "first 2 --three 3".split())
        expected = parse_me_full_docstring("first", 2, 3)
        self.assertEqual(actual, expected)

    def test_function_default(self):
        parser = FunctionParser()
        actual = parser(parse_me_full_docstring, "first 2".split())
        expected = parse_me_full_docstring("first", 2)
        self.assertEqual(actual, expected)

    def test_function_delimiter_chars(self):
        parser = FunctionParser()
        with captured_output() as (out, _):
            with self.assertRaises(SystemExit):
                parser(
                    different_delimiter_chars, "--help".split(), delimiter_chars="--"
                )
            help_message = out.getvalue()
        self.assertIn("this one is a no brainer even with dashes", help_message)
        self.assertIn(
            "noticed you're missing docstring for two and I'm multiline " "too!",
            help_message,
        )


class TestMethodParser(unittest.TestCase):
    def test_create_parser_on_function(self):
        parser = i_am_parseable.parser
        self.assertEqual(parser.description, "I too want to be parseable.")
        self.assertEqual(parser.call(args="yes 2 --three 3".split()), ("yesyes", 9))

    def test_create_parser_on_method(self):
        parser = Dummy.multiply_all.parser
        self.assertEqual(parser.description, "Will multiply everything!")
        self.assertEqual(parser.call(Dummy(12), ["2"]), 48)

    def test_create_parser_on_classmethod(self):
        parser = Dummy.mult.parser
        self.assertEqual(parser.call(Dummy, "2 --e 2".split()), 4)

    def test_create_parser_on_init(self):
        parser = NeedParseClassDecorator.__init__.parser
        self.assertRaises(ParseThisException, parser.call, None, ["2"])

    def test_create_parser_rename(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.could_you_parse_me.parser
        # at this stage the '_' aren't replaced yet
        self.assertEqual(parser.get_name(), "could_you_parse_me")

    def test_create_parser_default_name(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.rename_me_please.parser
        self.assertEqual(parser.get_name(), "new-name")


class TestClassParser(unittest.TestCase):
    def test_parse_class_description(self):
        self.assertEqual(NeedParsing.parser.description, "Hello World")
        self.assertEqual(
            ShowMyDocstring.parser.description, "This should be the parser description"
        )

    def test_parse_class_add_parser(self):
        self.assertTrue(hasattr(NeedParsing, "parser"))
        self.assertTrue(hasattr(NeedParsing(12), "parser"))
        self.assertTrue(hasattr(ShowMyDocstring, "parser"))

    def test_parse_class_subparsers(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 multiply-self-arg 2".split()), 24)
        self.assertEqual(
            parser.call("12 could-you-parse-me yes 2 --three 4".split()), ("yesyes", 16)
        )

    def test_parse_class_expose_private_method(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 private-method 2".split()), 24)

    def test_parse_class_expose_special_method(self):
        parser = NeedParsing.parser
        self.assertEqual(parser.call("12 str".split()), "12")

    def test_parse_class_do_not_expose_private_methods(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                ShowMyDocstring.parser.parse_args("will-not-appear 12".split())
            with self.assertRaises(SystemExit):
                ShowMyDocstring.parser.parse_args("str".split())

    def test_parse_class_method_is_still_parseable(self):
        need_parsing = NeedParsing(12)
        parser = need_parsing.could_you_parse_me.parser
        self.assertEqual(
            parser.call(need_parsing, "yes 2 --three 3".split()), ("yesyes", 9)
        )

    def test_parse_class_init_need_decoration(self):
        with self.assertRaises(ParseThisException):
            NeedInitDecorator.parser.call("do-stuff 12".split())

    def test_parse_class_need_init_decorator_with_instance(self):
        instance = NeedInitDecorator(2)
        self.assertEqual(
            NeedInitDecorator.parser.call("do-stuff 12".split(), instance), 12
        )
        self.assertEqual(
            NeedInitDecorator.parser.call("do-stuff 12 --div 3".split(), instance), 8
        )

    def test_parse_class_classmethod_are_not_sub_command(self):
        with captured_output():
            with self.assertRaises(SystemExit):
                NeedParsing.parser.call("12 parse-me-if-you-can one 2")


if __name__ == "__main__":
    unittest.main()
