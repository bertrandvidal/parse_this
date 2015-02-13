from functools import wraps
from inspect import getargspec
from parse_this.core import (_check_types, _get_args_and_defaults,
    _get_arg_parser, _get_args_to_parse, _call, ParseThisError, Self, Class,
    NoDefault)
import argparse
import sys

__all__ = ["Self", "Class", "ParseThisError", "parse_this", "create_parser",
           "parse_class"]


def parse_this(func, types, args=None, params_delim=":"):
    """Create an ArgumentParser for the given function converting the command line
        arguments according to the list of types.

    Args:
        func: the function for which the command line arguments to be parsed
        types: a list of types - as accepted by argparse - that will be used to
            convert the command line arguments
        args: a list of arguments to be parsed if None sys.argv is used
        params_delim: characters used to separate the parameters from their
        help message in the docstring. Defaults to ':'
    """
    (func_args, _, __, defaults) = getargspec(func)
    types, func_args = _check_types(types, func_args, defaults)
    args_and_defaults = _get_args_and_defaults(func_args, defaults)
    parser = _get_arg_parser(func, types, args_and_defaults, params_delim)
    arguments = parser.parse_args(_get_args_to_parse(args, sys.argv))
    return _call(func, func_args, arguments)


class create_parser(object):
    """Creates an argument parser for the decorated function."""

    def __init__(self, *types, **options):
        """
        Args:
            types: vargs list of types to which the command line arguments should
            be converted to
            options: options to pass to create the parser. Possible values are:
                -params_delim: characters used to separate the parameters from their
                help message in the docstring. Defaults to ':'
                -name: name that will be used for the parser when used in a
                class decorated with `parse_class`. If not provided the name
                of the method will be used
        """
        self._types = types
        self._params_delim = options.get("params_delim", ":")
        self._name = options.get("name", None)

    def __call__(self, func):
        """Add an argument parser attribute `parser` to the decorated function.

        Args:
            func: the function for which we want to create an argument parser
        """
        if not hasattr(func, "parser"):
            (func_args, _, _, defaults) = getargspec(func)
            self._types, func_args = _check_types(
                self._types, func_args, defaults)
            args_and_defaults = _get_args_and_defaults(func_args, defaults)
            parser = _get_arg_parser(func, self._types, args_and_defaults,
                                     self._params_delim)
            parser._name = self._name
            func.parser = parser

        @wraps(func)
        def decorated(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated


class _HelpAction(argparse._HelpAction):
    """Custom HelpAction to display help from all subparsers.

    This allows to have the help for all sub-commands when invoking:
    '<script.py> --help' rather than a somewhat incomplete help message only
    describing the name of the sub-commands.
    Note: taken from http://stackoverflow.com/a/24122778/2003420
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # Print help for the parser this class is linked to
        parser.print_help()
        # Retrieve sub-parsers of the given parser
        subparsers_actions = [action for action in parser._actions
                              if isinstance(action, argparse._SubParsersAction)]
        for subparser_action in subparsers_actions:
            # Get all subparsers and print their help
            for choice, subparser in subparser_action.choices.items():
                print("** Command '{}' **".format(choice))
                print("{}\n".format(subparser.format_help()))
        parser.exit()


class parse_class(object):
    """Allows to create a global argument parser for a class along with
    subparsers with each if its properly decorated methods."""

    def __init__(self, description=None, parse_private=False):
        """

        Args:
            description: give a specific description for the top level parser,
            if not specified it will be the class docstring.
            parse_private: specifies whether or not 'private' methods should be
            parsed, defaults to False
        """
        self._description = description
        self._parse_private = parse_private
        self._cls = None

    def __call__(self, cls):
        """
        Args:
            cls: class to get decorated
        """
        self._cls = cls
        init_parser, methods_to_parse = self._get_parseable_methods(cls)
        return self._get_class_parser(init_parser, methods_to_parse, cls)

    def _get_parseable_methods(self, cls):
        """Return all methods of cls that are parseable i.e. have been decorated
        by '@create_parser'.

        Args:
            cls: the class currently being decorated

        Returns:
            a 2-tuple with the parser of the __init__ method if any and a dict
            of the form {'method_name': associated_parser}
        """
        init_parser = None
        methods_to_parse = {}
        for name, obj in vars(cls).items():
            # Every callable object that has a 'parser' attribute will be
            # added as a subparser.
            # This won't work for classmethods because reference to
            # classmethods are only possible once the class has been defined
            if callable(obj) and hasattr(obj, "parser"):
                if name == "__init__":
                    # If we find the decorated __init__ method it will be
                    # used as the top level parser
                    init_parser = obj.parser
                else:
                    methods_to_parse[obj.__name__] = obj.parser
        return (init_parser, methods_to_parse)

    def _add_sub_parsers(self, top_level_parser, methods_to_parse, class_name):
        """Add all the sub-parsers to the top_level_parser.

        Args:
            top_level_parser: the top level parser
            methods_to_parse: dict of method name pointing to their associated
            argument parser
            class_name: name of the decorated class

        Returns:
            a dict of registered name of the parser i.e. sub command name
            pointing to the method real name
        """
        description = "Accessible methods of {}".format(class_name)
        sub_parsers = top_level_parser.add_subparsers(description=description,
                                                      dest="method")
        # Holds the mapping between the name registered for the parser
        # and the method real name. It is useful in the 'inner_call'
        # method retrieve the real method
        parser_name_to_method_name = {}
        for method_name, parser in methods_to_parse.items():
            # We use the name provided in 'create_parser` or the name of the
            # decorated method
            parser_name = parser._name or method_name
            # Make the method name compatible for the argument parsing
            if parser_name.startswith("_"):
                if not self._parse_private:
                    # We skip private methods if the caller asked not to
                    # parse them
                    continue
                # 'Private' methods are exposed without their leading or
                # trailing '_'s. Also works for 'special' methods.
                parser_name = parser_name.strip("_")
            parser_name = parser_name.replace("_", "-")
            parser_name_to_method_name[parser_name] = method_name
            sub_parsers.add_parser(parser_name, parents=[parser],
                                   add_help=False,
                                   description=parser.description)
        return parser_name_to_method_name

    def _get_class_parser(self, init_parser, methods_to_parse, cls):
        """Creates the complete argument parser for the decorated class.

        Args:
            init_parser: argument parser for the __init__ method or None
            methods_to_parse: dict of method name pointing to their associated
            argument parser
            cls: the class we are decorating

        Returns:
            The decorated class with an added attribute 'parser'
        """
        top_level_parents = [init_parser] if init_parser else []
        top_level_parser = argparse.ArgumentParser(description=self._description or cls.__doc__,
                                                   parents=top_level_parents,
                                                   add_help=False,
                                                   conflict_handler="resolve")
        top_level_parser.add_argument("-h", "--help", action=_HelpAction,
                                      help="Display this help message")
        parser_name_to_method_name = self._add_sub_parsers(top_level_parser,
                                                           methods_to_parse,
                                                           cls.__name__)
        # Update the dict with the __init__ method so we can instantiate
        # the decorated class
        if init_parser:
            parser_name_to_method_name["__init__"] = "__init__"
        top_level_parser.call = self._get_parser_call_method(parser_name_to_method_name)
        cls.parser = top_level_parser
        return cls

    def _get_parser_call_method(self, parser_name_to_method_name):
        """Return the parser special method 'call' that handles sub-command calling.

        Args:
            parser_name_to_method_name: mapping of the parser registered name
            to the method it is linked to
        """
        def inner_call(args=None, instance=None):
            """Allows to call the method invoked from the command line or
            provided argument.

            Args:
                argument: list of agurments to parse, defaults to command line
                arguments
                instance: an instance of the decorated class. If instance is
                None, the default, and __init__ is decorated the object will be
                instantiated on the fly from the command line arguments
            """
            namespace = self._cls.parser.parse_args(args or sys.argv[1:])
            if instance is None:
                # If the __init__ method is not part of the method to
                # decorate we cannot instantiate the class
                if "__init__" not in parser_name_to_method_name:
                    raise ParseThisError(("'__init__' method is not decorated. "
                                          "Please provide an instance to "
                                          "'{}.parser.call' or decorate the "
                                          "'__init___' method with "
                                          "'create_parser'".format(self._cls.__name__)))
                # We instantiate the class from the command line agurments
                instance = self._call_method_from_namespace(self._cls,
                                                            "__init__",
                                                            namespace)
            method_name = parser_name_to_method_name[namespace.method]
            return self._call_method_from_namespace(instance, method_name,
                                                    namespace)
        return inner_call

    def _call_method_from_namespace(self, obj, method_name, namespace):
        """Call the method, retrieved from obj, with the correct arguments via
        the namespace

        Args:
            obj: any kind of object
            method_name: method to be called
            namespace: an argparse.Namespace object containing parser command
            line arguments
        """
        method = getattr(obj, method_name)
        method_parser = method.parser
        # Retrieve the 'action' destination of the method parser i.e. its
        # argument name
        actions = [action.dest for action in method_parser._actions if not
                   isinstance(action, argparse._HelpAction)]
        arguments = {arg_name: getattr(namespace, arg_name)
                     for arg_name in actions}
        if method_name == "__init__":
            return obj(**arguments)
        return method(**arguments)

