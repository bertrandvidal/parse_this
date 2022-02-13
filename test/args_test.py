import unittest

from parse_this.args import _get_args_and_defaults, _get_args_to_parse
from parse_this.values import _NO_DEFAULT


class TestArgs(unittest.TestCase):
    def test_get_args_and_defaults_fill_no_default(self):
        args_and_defaults = _get_args_and_defaults(
            ["first", "second", "third"], ("default_value",)
        )
        self.assertListEqual(
            args_and_defaults,
            [
                ("first", _NO_DEFAULT),
                ("second", _NO_DEFAULT),
                ("third", "default_value"),
            ],
        )

    def test_get_args_and_defaults_no_args(self):
        self.assertListEqual(_get_args_and_defaults([], ()), [])

    def test_get_args_and_defaults_no_default(self):
        self.assertListEqual(
            _get_args_and_defaults(["first", "second"], ()),
            [("first", _NO_DEFAULT), ("second", _NO_DEFAULT)],
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


if __name__ == "__main__":
    unittest.main()
