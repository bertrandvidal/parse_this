from parse_this.core import (_get_args_and_defaults, NoDefault,
                             _get_default_help_message)
import unittest


def no_docstring():
    pass


def with_args(a, b):
    pass


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


if __name__ == "__main__":
    unittest.main()
