import logging

from parse_this.parsers import ClassParser, FunctionParser, MethodParser

_LOG = logging.getLogger(__name__)


parse_this = FunctionParser()

create_parser = MethodParser

parse_class = ClassParser
