import unittest

from parse_this.exception import ParseThisException
from parse_this.types import _check_types


class TestCore(unittest.TestCase):
    def test_check_types_not_enough_types_provided(self):
        self.assertRaises(
            ParseThisException, _check_types, "function", {}, ["i_dont_have_a_type"], ()
        )

    def test_check_types_too_many_types_provided(self):
        self.assertRaises(
            ParseThisException,
            _check_types,
            "function",
            {"a": int, "b": int},
            ["i_am_alone"],
            (),
        )

    def test_check_types_with_default(self):
        func_args = ["i_am_alone", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int, "i_have_a_default_value": str},
                func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_with_default_type_not_specified(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function", {"i_am_an_int": int}, func_args, ("default_value",)
            ),
            func_args,
        )

    def test_check_types_remove_self(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int},
                ["self"] + func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_remove_class(self):
        func_args = ["i_am_an_int", "i_have_a_default_value"]
        self.assertEqual(
            _check_types(
                "function",
                {"i_am_an_int": int},
                ["cls"] + func_args,
                ("default_value",),
            ),
            func_args,
        )

    def test_check_types_no_args(self):
        self.assertEqual(_check_types("function", {}, [], ()), [])

    def test_check_types_return_annotation(self):
        self.assertEqual(_check_types("function", {"return": int}, [], ()), [])


if __name__ == "__main__":
    unittest.main()
