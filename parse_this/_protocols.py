from argparse import ArgumentParser
from typing import Any, Protocol


class _Named(Protocol):
    """Any callable that carries standard function metadata."""

    __name__: str
    __doc__: str | None

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class _ParsedCallable(_Named, Protocol):
    """A callable that has been decorated by @create_parser (has .parser)."""

    parser: ArgumentParser
