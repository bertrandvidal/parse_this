import sys
import unittest

from parse_this import (_get_args_and_defaults, NoDefault, _get_args_to_parse,
                        _check_types, _get_arg_parser)


def parse_me(one, two, three=12):
  pass


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
    self.assertItemsEqual(_get_args_to_parse(None, ["arg"]), ["arg"])
    self.assertItemsEqual(_get_args_to_parse(None, ["arg", "--kwargs=12"]),
                          ["arg", "--kwargs=12"])
    self.assertItemsEqual(_get_args_to_parse([], []), [])
    self.assertItemsEqual(_get_args_to_parse(["arg", "--kwargs=12"], []),
                                             ["arg", "--kwargs=12"])

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


if __name__ == "__main__":
  unittest.main()
