from parse_this import create_parser, parse_class


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
