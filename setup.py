import os
import sys

from setuptools import setup

pure_python = any(
    [
        sys.implementation.name != "cpython",
        os.environ.get("PY_BENCODE2_PURE_PYTHON") == "1",
    ]
)

if pure_python:
    setup()
else:
    setup(cmake_source_dir=".")
