#!/usr/bin/env python
import os
from setuptools import setup

README_PATH = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(README_PATH, "r") as README_FILE:
    README = README_FILE.read()

setup(
    name="parse_this",
    version="1.0.3",
    description=("Makes it easy to create a command line interface for any "
                 "function, method or classmethod.."),
    long_description=README,
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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    setup_requires=[
        "nose",
    ],
)
