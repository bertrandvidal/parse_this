import sys
import unittest

from parse_this import (_get_args_and_defaults, NoDefault, _get_args_to_parse,
                        _check_types, _get_arg_parser, parse_this, _prepare_doc,
                        create_parser, Self, Class, ParseThisError)


def parse_me(one, two, three=12):
    """Could use some parsing.

    Args:
      one: some stuff shouldn't be written down
      two: I can turn 2 syllables words into 6 syllables words
      three: I don't like the number three
    """
    return one * two, three * three


def parse_me_no_doc(one, two, three):
    return one * two, three * three


def will_you_dare_parse_me(one, two, three):
    """I am a sneaky function.

    Args:
      one: this one is a no brainer
      three: noticed you're missing docstring for two and
        I'm multiline too!
    """
    return one * two, three * three


class TestParseThis(unittest.TestCase):

    def test_get_args_and_default(self):
        args_and_defaults = _get_args_and_defaults(["first", "second", "third"],
                                                   ("default_value",
                                                    "other_default"))
        self.assertListEqual(args_and_defaults, [("first", NoDefault),
                                                 ("second", "default_value"),
                                                 ("third", "other_default")])
        self.assertListEqual(_get_args_and_defaults([], ()), [])

    def test_get_args_to_parse(self):
        self.assertListEqual(_get_args_to_parse(None, []), [])
        self.assertListEqual(
            _get_args_to_parse(None, ["prog", "arg"]), ["arg"])
        self.assertListEqual(_get_args_to_parse(None, ["prog", "arg",
                                                       "--kwargs=12"]),
                              ["arg", "--kwargs=12"])
        self.assertListEqual(_get_args_to_parse([], []), [])
        self.assertListEqual(_get_args_to_parse(["prog", "arg",
                                                 "--kwargs=12"], []),
                              ["prog", "arg", "--kwargs=12"])

    def test_prepare_doc(self):
        (description, help_msg) = _prepare_doc(parse_me,
                                               ["one", "two", "three"])
        self.assertEqual(description, "Could use some parsing.")
        self.assertEqual(help_msg, {"one":"some stuff shouldn't be written down",
                                    "two":"I can turn 2 syllables words into 6 syllables words",
                                    "three": "I don't like the number three"})

    def test_prepare_doc_no_docstring(self):
        (description, help_msg) = _prepare_doc(parse_me_no_doc,
                                               ["one", "two", "three"])
        self.assertEqual(description, "Argument parsing for parse_me_no_doc")
        self.assertEqual(help_msg, {"one": "Help message for one",
                                    "two":  "Help message for two",
                                    "three":  "Help message for three"})

    def test_prepare_doc_will_you_dare(self):
        (description, help_msg) = _prepare_doc(will_you_dare_parse_me,
                                               ["one", "two", "three"])
        self.assertEqual(description, "I am a sneaky function.")
        self.assertEqual(help_msg, {"one": "this one is a no brainer",
                                    "two": "Help message for two",
                                    "three": "noticed you're missing docstring for two and I'm multiline too!"})

    def test_check_types(self):
        self.assertRaises(ParseThisError, _check_types, [], ["arg_one"], ())
        self.assertRaises(ParseThisError, _check_types, [int, float],
                          ["arg_one"], ())
        try:
            _check_types([], [], ())
            _check_types([int, int], ["arg_one", "arg_two"], ())
            _check_types([int, int], ["arg_one", "arg_two"], (12,))
            _check_types([int], ["arg_one", "arg_two"], (12,))
            _check_types([Self, int, int], ["self", "arg_one", "arg_two"], ())
        except Exception as exception:
            self.fail("_check_types should not have raised: %s" % exception)

    def test_namespace_no_option(self):
        parser = _get_arg_parser(parse_me, [str, int], [("one", NoDefault),
                                                        ("two", NoDefault),
                                                        ("three", 12)])
        namespace = parser.parse_args("yes 42".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 42)
        self.assertEqual(namespace.three, 12)

    def test_namespace(self):
        parser = _get_arg_parser(parse_me, [str, int], [("one", NoDefault),
                                                        ("two", NoDefault),
                                                        ("three", 12)])
        namespace = parser.parse_args("no 12 --three=23".split())
        self.assertEqual(namespace.one, "no")
        self.assertEqual(namespace.two, 12)
        self.assertEqual(namespace.three, 23)

    def test_return_value(self):
        self.assertEqual(parse_this(parse_me, [str, int], "yes 2".split()),
                          ("yesyes", 144))
        self.assertEqual(parse_this(parse_me, [str, int],
                                     "no 3 --three 2".split()),
                          ("nonono", 4))


@create_parser(str, int)
def iam_parseable(one, two, three=12):
    """I too want to be parseable.

    Args:
      one: the one and only
      two: for the money
      three: don't like the number three
    """
    return one * two, three * three


class NeedParsing(object):

    @create_parser(Self, str, int)
    def could_you_parse_me(self, one, two, three=12):
        """I would like some arg parsing please.

        Args:
          one: and only one
          two: will never be first
          three: I don't like the number three
        """
        return one * two, three * three

    @classmethod
    @create_parser(Class, str, int)
    def parse_me_if_you_can(cls, one, two, three=12):
        return one * two, three * three


class TestParseable(unittest.TestCase):

    def test_parseable(self):
        parser = iam_parseable.parser
        namespace = parser.parse_args("yes 2 --three 3".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 2)
        self.assertEqual(namespace.three, 3)
        self.assertEqual(iam_parseable("yes", 2, 3), ("yesyes", 9))

    def test_parseable_method(self):
        need_parsing = NeedParsing()
        parser = need_parsing.could_you_parse_me.parser
        namespace = parser.parse_args("yes 2 --three 3".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 2)
        self.assertEqual(namespace.three, 3)
        self.assertEqual(
            need_parsing.could_you_parse_me("yes", 2, 3), ("yesyes", 9))

    def test_parseable_class(self):
        parser = NeedParsing.parse_me_if_you_can.parser
        namespace = parser.parse_args("yes 2 --three 3".split())
        self.assertEqual(namespace.one, "yes")
        self.assertEqual(namespace.two, 2)
        self.assertEqual(namespace.three, 3)
        self.assertEqual(NeedParsing.parse_me_if_you_can("yes", 2, 3),
                         ("yesyes", 9))


if __name__ == "__main__":
    unittest.main()
