from parse_this import create_parser, parse_class


def no_docstring():
    pass


def with_args(a, b):
    pass


def blank_line_in_wrong_place(one: int, two: int):
    """I put the blank line after arguments ...

    Args:
        one: this help is #1

        two: this once won't appear sadly
    """
    return one * two


def parse_me_full_docstring(one: str, two: int, three: int = 12):
    """Could use some parsing.

    Args:
        one: some stuff shouldn't be written down
        two: I can turn 2 syllables words into 6 syllables words
        three: I don't like the number three

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


def parse_me_no_docstring(one: int, two: int, three: int):
    return one * two, three * three


def multiline_docstring(one: int, two: int, three: int):
    """I am a sneaky function.

    Args:
        one: this one is a no brainer
        three: noticed you're missing docstring for two and
          I'm multiline too!

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


def different_delimiter_chars(one: int, two: int, three: int):
    """I am a sneaky function.

    Args:
        one -- this one is a no brainer even with dashes
        three -- noticed you're missing docstring for two and
          I'm multiline too!

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


def parse_me(one: str, two: int, three: int = 12):
    """Could use some parsing.

    Args:
        one: some stuff shouldn't be written down
        two: I can turn 2 syllables words into 6 syllables words
        three: I don't like the number three

    Returns:
        the first string argument concatenated with itself 'two' times and the
        last parameters multiplied by itself
    """
    return one * two, three * three


@create_parser()
def concatenate_string(string: str, nb_concat: int):
    return string * nb_concat


@create_parser()
def has_none_default_value(a: int, b: str = None):
    return a, b


@create_parser()
def has_flags(a: int, b: bool = False):
    return a, b


@create_parser()
def has_bool_arguments(a: bool):
    return a


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


@parse_class(parse_private=True)
class ParseableWithPrivateMethod(object):
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


@create_parser()
def i_am_parseable(one: str, two: int, three: int = 12):
    """I too want to be parseable.

    Args:
      one: the one and only
      two: for the money
      three: don't like the number three
    """
    return one * two, three * three


class Dummy(object):
    def __init__(self, a):
        self._a = a

    @create_parser(delimiter_chars="--")
    def multiply_all(self, b: int, c: int = 2):
        """Will multiply everything!

        Args:
            b -- the Queen B
            c -- a useless value

        Returns:
            Everything multiplied
        """
        return self._a * b * c

    @classmethod
    @create_parser()
    def mult(cls, d: int, e: int = 2):
        return d * e


class NeedParseClassDecorator(object):
    @create_parser()
    def __init__(self, a: int):
        self._a = a


@parse_class(description="Hello World", parse_private=True)
class NeedParsing(object):
    """This will be used as the parser description."""

    @create_parser()
    def __init__(self, four: int):
        """
        Args:
            four: an int that will be used to multiply stuff
        """
        self._four = four

    @create_parser()
    def multiply_self_arg(self, num: int):
        return self._four * num

    @create_parser()
    def _private_method(self, num: int):
        return self._four * num

    @create_parser()
    def __str__(self):
        return str(self._four)

    @create_parser()
    def could_you_parse_me(self, one: str, two: int, three: int = 12):
        """I would like some arg parsing please.

        Args:
          one: and only one
          two: will never be first
          three: I don't like the number three
        """
        return one * two, three * three

    @classmethod
    @create_parser()
    def parse_me_if_you_can(cls, one: str, two: int, three: int = 12):
        return one * two, three * three


@parse_class()
class ShowMyDocstring(object):
    """This should be the parser description"""

    @create_parser()
    def _will_not_appear(self, num: int):
        return num * num

    @create_parser()
    def __str__(self):
        return self.__class__.__name__


@parse_class()
class NeedInitDecorator(object):
    def __init__(self, val: int):
        self._val = val

    @create_parser()
    def do_stuff(self, num: int, div: int = 2):
        return self._val * num / div
