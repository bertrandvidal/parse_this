#!/usr/bin/env python
import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), "r") as readme_file:
    readme = readme_file.read()

setup(
    name = "parse_this",
    version = "0.3.1",
    description = "Makes it easy to create a command line interface for any function, method or classmethod..",
    long_description = readme,
    py_modules = ["parse_this", "parse_this_test"],
    author = "Bertrand Vidal",
    author_email = "vidal.bertrand@gmail.com",
    download_url = "https://pypi.python.org/pypi/parse_this",
    url = "https://github.com/bertrandvidal/parse_this",
    classifiers = [
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    setup_requires = [
        "nose",
    ],
)
