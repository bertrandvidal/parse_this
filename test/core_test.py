import unittest

from parse_this import create_parser
from parse_this.exception import ParseThisException
from test.helpers import has_bool_arguments, has_flags, has_none_default_value


class TestCore(unittest.TestCase):
    def test_get_arg_parser_bool_argument(self):
        self.assertEqual(has_bool_arguments.parser.call(args=[]), True)
        self.assertEqual(has_bool_arguments.parser.call(args=["--a"]), False)

    def test_get_arg_parser_bool_default_value(self):
        self.assertEqual(has_flags.parser.call(args=["12"]), (12, False))
        self.assertEqual(has_flags.parser.call(args=["12", "--b"]), (12, True))

    def test_get_arg_parser_none_default_value_without_type(self):
        with self.assertRaises(ParseThisException):

            @create_parser(int)
            def have_none_default_value(a: int, b=None):
                pass

    def test_get_arg_parser_with_none_default_value(self):
        self.assertEqual(has_none_default_value.parser.call(args=["12"]), (12, None))
        self.assertEqual(
            has_none_default_value.parser.call(args=["12", "--b", "yes"]), (12, "yes")
        )


if __name__ == "__main__":
    unittest.main()
