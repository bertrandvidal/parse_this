import unittest

from parse_this import parse_this
from test.helpers import (
    parse_me,
)


class TestParseThis(unittest.TestCase):
    def test_parse_this_return_value(self):
        self.assertEqual(parse_this(parse_me, "yes 2".split()), ("yesyes", 144))
        self.assertEqual(parse_this(parse_me, "no 3 --three 2".split()), ("nonono", 4))


if __name__ == "__main__":
    unittest.main()
