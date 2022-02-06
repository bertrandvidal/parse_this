import unittest

from parse_this import create_parser, parse_class, parse_this
from parse_this.exception import ParseThisException
from test.utils import captured_output


def parse_me(one: str, two: int, three: int = 12):
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


class TestParseThis(unittest.TestCase):
    def test_parse_this_return_value(self):
        self.assertEqual(parse_this(parse_me, "yes 2".split()), ("yesyes", 144))
        self.assertEqual(parse_this(parse_me, "no 3 --three 2".split()), ("nonono", 4))


@create_parser()
def i_am_parseable(one: str, two: int, three: int = 12):
    """I too want to be parseable.

    Args:
      one: the one and only
      two: for the money
      three: don't like the number three
    """
    return one * two, three * three


class Dummy(object):
    def __init__(self, a):
        self._a = a

    @create_parser(delimiter_chars="--")
    def multiply_all(self, b: int, c: int = 2):
        """Will multiply everything!

        Args:
            b -- the Queen B
            c -- a useless value

        Returns:
            Everything multiplied
        """
        return self._a * b * c

    @classmethod
    @create_parser()
    def mult(cls, d: int, e: int = 2):
        return d * e


class NeedParseClassDecorator(object):
    @create_parser()
    def __init__(self, a: int):
        self._a = a


class TestCreateParser(unittest.TestCase):
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


@parse_class(description="Hello World", parse_private=True)
class NeedParsing(object):

    """This will be used as the parser description."""

    @create_parser()
    def __init__(self, four: int):
        """
        Args:
            four: an int that will be used to multiply stuff
        """
        self._four = four

    @create_parser()
    def multiply_self_arg(self, num: int):
        return self._four * num

    @create_parser()
    def _private_method(self, num: int):
        return self._four * num

    @create_parser()
    def __str__(self):
        return str(self._four)

    @create_parser()
    def could_you_parse_me(self, one: str, two: int, three: int = 12):
        """I would like some arg parsing please.

        Args:
          one: and only one
          two: will never be first
          three: I don't like the number three
        """
        return one * two, three * three

    @classmethod
    @create_parser()
    def parse_me_if_you_can(cls, one: str, two: int, three: int = 12):
        return one * two, three * three


@parse_class()
class ShowMyDocstring(object):

    """This should be the parser description"""

    @create_parser()
    def _will_not_appear(self, num: int):
        return num * num

    @create_parser()
    def __str__(self):
        return self.__class__.__name__


@parse_class()
class NeedInitDecorator(object):
    def __init__(self, val: int):
        self._val = val

    @create_parser()
    def do_stuff(self, num: int, div: int = 2):
        return self._val * num / div


class TestParseClass(unittest.TestCase):
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
