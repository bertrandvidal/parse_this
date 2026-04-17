"""End-to-end coverage for the four supported docstring styles.

Each style has a fixture function carrying a description plus per-arg
help written in that style. We exercise both auto-detection (the
default) and explicit overrides via the ``docstring_style`` kwarg, and
make sure the parser falls back gracefully on unknown styles and
unparseable docstrings.
"""

import unittest

from parse_this import create_parser, parse_class
from parse_this.exception import ParseThisException
from parse_this.help.description import prepare_doc


def google(one: int, two: str):
    """Google-style demo.

    Args:
        one: first value
        two: second value
    """
    return one, two


def numpy_doc(one: int, two: str):
    """NumPy-style demo.

    Parameters
    ----------
    one : int
        first value
    two : str
        second value
    """
    return one, two


def rest(one: int, two: str):
    """reST-style demo.

    :param one: first value
    :param two: second value
    """
    return one, two


def epytext(one: int, two: str):
    """Epytext-style demo.

    @param one: first value
    @param two: second value
    """
    return one, two


def google_partial(one: int, two: str):
    """Google-style demo with a missing arg.

    Args:
        one: first value
    """
    return one, two


class TestAutoDetection(unittest.TestCase):
    def test_google_autodetect(self):
        description, help_msg = prepare_doc(google, ["one", "two"])
        self.assertEqual(description, "Google-style demo.")
        self.assertEqual(help_msg, {"one": "first value", "two": "second value"})

    def test_numpy_autodetect(self):
        description, help_msg = prepare_doc(numpy_doc, ["one", "two"])
        self.assertEqual(description, "NumPy-style demo.")
        self.assertEqual(help_msg, {"one": "first value", "two": "second value"})

    def test_rest_autodetect(self):
        description, help_msg = prepare_doc(rest, ["one", "two"])
        self.assertEqual(description, "reST-style demo.")
        self.assertEqual(help_msg, {"one": "first value", "two": "second value"})

    def test_epytext_autodetect(self):
        description, help_msg = prepare_doc(epytext, ["one", "two"])
        self.assertEqual(description, "Epytext-style demo.")
        self.assertEqual(help_msg, {"one": "first value", "two": "second value"})


class TestExplicitStyleOverride(unittest.TestCase):
    def test_explicit_google(self):
        _, help_msg = prepare_doc(google, ["one", "two"], style="google")
        self.assertEqual(help_msg["one"], "first value")

    def test_explicit_numpy(self):
        _, help_msg = prepare_doc(numpy_doc, ["one", "two"], style="numpy")
        self.assertEqual(help_msg["one"], "first value")

    def test_explicit_rest(self):
        _, help_msg = prepare_doc(rest, ["one", "two"], style="rest")
        self.assertEqual(help_msg["one"], "first value")

    def test_explicit_epytext(self):
        _, help_msg = prepare_doc(epytext, ["one", "two"], style="epytext")
        self.assertEqual(help_msg["one"], "first value")


class TestPartialDocstring(unittest.TestCase):
    def test_missing_param_falls_back_to_default_for_that_arg_only(self):
        description, help_msg = prepare_doc(google_partial, ["one", "two"])
        self.assertEqual(description, "Google-style demo with a missing arg.")
        self.assertEqual(help_msg["one"], "first value")
        self.assertEqual(help_msg["two"], "Help message for two")


class TestErrorHandling(unittest.TestCase):
    def test_unknown_style_raises_parse_this_exception(self):
        with self.assertRaises(ParseThisException) as ctx:
            prepare_doc(google, ["one", "two"], style="klingon")
        msg = str(ctx.exception)
        self.assertIn("klingon", msg)
        # Error lists every supported style so users know what's valid.
        for valid in ("auto", "google", "numpy", "rest", "epytext"):
            self.assertIn(valid, msg)

    def test_malformed_docstring_falls_back_to_defaults(self):
        # docstring_parser raises ParseError on a stray "::" outside of
        # any valid directive when forced into the reST parser. We use
        # the explicit "rest" style so auto-detect can't sneak past it.
        def broken(one: int):
            """Bad rest.

            :: this is wrong syntax
            :param: missing name
            """

        description, help_msg = prepare_doc(broken, ["one"], style="rest")
        # Decoration must not crash; the help dict should fall back to
        # the default per-arg messages produced by _get_default_help_message.
        self.assertEqual(description, "Argument parsing for broken")
        self.assertEqual(help_msg, {"one": "Help message for one"})


class TestDocstringStyleKwargFlow(unittest.TestCase):
    def test_create_parser_passes_style_to_prepare_doc(self):
        @create_parser(docstring_style="numpy")
        def numpy_target(one: int, two: str):
            """NumPy demo.

            Parameters
            ----------
            one : int
                first value
            two : str
                second value
            """
            return one, two

        parser = numpy_target.parser
        self.assertEqual(parser.description, "NumPy demo.")
        actions_by_dest = {a.dest: a for a in parser._actions}
        self.assertEqual(actions_by_dest["one"].help, "first value")
        self.assertEqual(actions_by_dest["two"].help, "second value")

    def test_create_parser_explicit_style_mismatch_falls_back(self):
        # Decorating a Google-style docstring with style="numpy" should
        # leave the per-arg help as defaults — docstring_parser cannot
        # extract Args: blocks via the NumPy parser.
        @create_parser(docstring_style="numpy")
        def google_target(one: int, two: str):
            """Google demo.

            Args:
                one: first value
                two: second value
            """
            return one, two

        actions_by_dest = {a.dest: a for a in google_target.parser._actions}
        self.assertEqual(actions_by_dest["one"].help, "Help message for one")
        self.assertEqual(actions_by_dest["two"].help, "Help message for two")

    def test_parse_class_methods_use_their_own_style(self):
        @parse_class()
        class Mixed(object):
            """A class with two methods documented in two styles."""

            @create_parser(docstring_style="google")
            def __init__(self, base: int):
                """Init.

                Args:
                    base: starting value
                """
                self._base = base

            @create_parser(docstring_style="numpy")
            def add(self, n: int):
                """NumPy add.

                Parameters
                ----------
                n : int
                    value to add
                """
                return self._base + n

            @create_parser(docstring_style="rest")
            def mul(self, n: int):
                """reST mul.

                :param n: value to multiply
                """
                return self._base * n

        add_parser = Mixed.add.parser
        mul_parser = Mixed.mul.parser
        add_actions = {a.dest: a for a in add_parser._actions}
        mul_actions = {a.dest: a for a in mul_parser._actions}
        self.assertEqual(add_actions["n"].help, "value to add")
        self.assertEqual(mul_actions["n"].help, "value to multiply")
        # End-to-end dispatch using the top-level class parser.
        self.assertEqual(Mixed.parser.call("10 add 5".split()), 15)  # ty:ignore[unresolved-attribute]
        self.assertEqual(Mixed.parser.call("10 mul 5".split()), 50)  # ty:ignore[unresolved-attribute]


if __name__ == "__main__":
    unittest.main()
