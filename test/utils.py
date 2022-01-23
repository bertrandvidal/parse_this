import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def captured_output():
    """Allows to safely capture stdout and stderr in a context manager."""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
