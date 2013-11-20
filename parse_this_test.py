import sys
import unittest

from parse_this import _get_args_and_defaults, NoDefault, _get_args_to_parse


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
    self.assertItemsEqual(_get_args_to_parse(None, ["arg", "--kwargs=12"]), ["arg", "--kwargs=12"])
    self.assertItemsEqual(_get_args_to_parse([], []), [])
    self.assertItemsEqual(_get_args_to_parse(["arg", "--kwargs=12"], []),
                                             ["arg", "--kwargs=12"])


if __name__ == "__main__":
  unittest.main()
