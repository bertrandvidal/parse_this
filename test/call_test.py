import unittest
from collections import namedtuple

from parse_this import create_parser, parse_class
from parse_this.call import (
    _call,
    _call_method_from_namespace,
    _get_parser_call_method,
)
from parse_this.exception import ParseThisException


@parse_class()
class Parseable(object):
    @create_parser()
    def __init__(self, a: int):
        self._a = a

    @create_parser()
    def _private_method(self, b: int):
        return self._a * b

    def not_parseable(self, c: int):
        return self._a * c

    @create_parser()
    def parseable(self, d: int):
        return self._a * d

    @classmethod
    @create_parser()
    def cls_method(cls, e: int):
        return e * e


def parse_me_no_docstring(one: int, two: int, three: int):
    return one * two, three * three


@create_parser()
def concatenate_string(string: str, nb_concat: int):
    return string * nb_concat


class TestCall(unittest.TestCase):
    def test_get_parser_call_method_returns_callable(self):
        call_method = _get_parser_call_method(concatenate_string)
        self.assertTrue(callable(call_method))

    def test_get_parser_call_method_raise_on_init(self):
        call_method = _get_parser_call_method(Parseable.__init__)
        self.assertRaises(ParseThisException, call_method, None)

    def test_get_parser_call_method_execution(self):
        call_method = _get_parser_call_method(Parseable.parseable)
        self.assertEqual(call_method(Parseable(12), ["2"]), 24)

    def test_get_parser_call_method_on_function(self):
        call_method = _get_parser_call_method(concatenate_string)
        self.assertEqual(call_method(args="yes 2".split()), "yesyes")

    def test_call_on_parse_me_no_docstring(self):
        Namespace = namedtuple("Namespace", ["one", "two", "three"])
        fake_namespace = Namespace(**{"one": 2, "two": 12, "three": 3})
        self.assertEqual(
            _call(parse_me_no_docstring, ["one", "two", "three"], fake_namespace),
            (24, 9),
        )

    def test_call_method_from_namespace_create_instance(self):
        Namespace = namedtuple("Namespace", ["a"])
        fake_namespace = Namespace(a=2)
        parseable = _call_method_from_namespace(Parseable, "__init__", fake_namespace)
        self.assertIsInstance(parseable, Parseable)
        self.assertEqual(parseable._a, 2)

    def test_call_method_from_namespace_execution(self):
        Namespace = namedtuple("Namespace", ["d"])
        fake_namespace = Namespace(d=2)
        self.assertEqual(
            _call_method_from_namespace(Parseable(12), "parseable", fake_namespace), 24
        )


if __name__ == "__main__":
    unittest.main()
