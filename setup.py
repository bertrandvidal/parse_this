#!/usr/bin/env python
import os
from setuptools import setup

README_PATH = os.path.join(os.path.dirname(__file__), "README.md")
with open(README_PATH, "r") as README_FILE:
    README = README_FILE.read()

setup(
    name="parse_this",
    version="2.0.4",
    description=(
        "Makes it easy to create a command line interface for any "
        "function, method or classmethod.."
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["parse_this", "test"],
    author="Bertrand Vidal",
    author_email="vidal.bertrand@gmail.com",
    download_url="https://pypi.python.org/pypi/parse_this",
    url="https://github.com/bertrandvidal/parse_this",
    license="License :: MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
