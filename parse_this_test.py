import sys
import unittest

from parse_this import (_get_args_and_defaults, NoDefault, _get_args_to_parse,
                        _check_types, _get_arg_parser, parse_this, _prepare_doc)


def parse_me(one, two, three=12):
  """Could use some parsing.

  Args:
    one: some stuff shouldn't be written down
    two: I can turn 2 syllables words into 6 syllables words
    three: I don't like the number three
  """
  return one * two, three*three


class TestParseThis(unittest.TestCase):

  def test_get_args_and_default(self):
    args_and_defaults = _get_args_and_defaults(["first", "second", "third"],
                                               ("default_value","other_default"))
    self.assertItemsEqual(args_and_defaults, [("first", NoDefault),
                                              ("second", "default_value"),
                                              ("third", "other_default")])
    self.assertItemsEqual(_get_args_and_defaults([], ()), [])

  def test_get_args_to_parse(self):
    self.assertItemsEqual(_get_args_to_parse(None, []), [])
    self.assertItemsEqual(_get_args_to_parse(None, ["prog", "arg"]), ["arg"])
    self.assertItemsEqual(_get_args_to_parse(None, ["prog", "arg", "--kwargs=12"]),
                          ["arg", "--kwargs=12"])
    self.assertItemsEqual(_get_args_to_parse([], []), [])
    self.assertItemsEqual(_get_args_to_parse(["prog", "arg", "--kwargs=12"], []),
                                             ["prog", "arg", "--kwargs=12"])

  def test_prepare_doc(self):
    (description, help_msg) = _prepare_doc(parse_me.__doc__,
                                           ["one","two","three"])
    self.assertEquals(description, "Could use some parsing.")
    self.assertItemsEqual(help_msg, ["some stuff shouldn't be written down",
                                     "I can turn 2 syllables words into 6 syllables words",
                                     "I don't like the number three"])

  def test_check_types(self):
    self.assertRaises(AssertionError, _check_types, [], ["arg_one"], ())
    self.assertRaises(AssertionError, _check_types, [int, float], ["arg_one"],
                      ())
    try:
      _check_types([], [], ())
      _check_types([int, int], ["arg_one", "arg_two"], ())
      _check_types([int, int], ["arg_one", "arg_two"], (12,))
      _check_types([int], ["arg_one", "arg_two"], (12,))
    except Exception, exception:
      self.fail("_check_types should have raised: %s" % exception)

  def test_namespace_no_option(self):
    parser = _get_arg_parser(parse_me, [str, int], [("one", NoDefault),
                                                    ("two", NoDefault),
                                                    ("three",12)])
    namespace = parser.parse_args("yes 42".split())
    self.assertEquals(namespace.one, "yes")
    self.assertEquals(namespace.two, 42)
    self.assertEquals(namespace.three, 12)

  def test_namespace(self):
    parser = _get_arg_parser(parse_me, [str, int], [("one", NoDefault),
                                                    ("two", NoDefault),
                                                    ("three", 12)])
    namespace =parser.parse_args("no 12 --three=23".split())
    self.assertEquals(namespace.one, "no")
    self.assertEquals(namespace.two, 12)
    self.assertEquals(namespace.three, 23)

  def test_return_value(self):
    self.assertEquals(parse_this(parse_me, [str, int], "yes 2".split()),
                      ("yesyes", 144))
    self.assertEquals(parse_this(parse_me, [str, int], "no 3 --three 2".split()),
                      ("nonono", 4))


if __name__ == "__main__":
  unittest.main()
