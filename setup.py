import os
from setuptools import setup

from Cython.Build import cythonize


def get_readme():
    """Load README.rst for display on PyPI."""
    with open("readme.md", "r", encoding="utf-8") as f:
        return f.read()


if os.environ.get("COV") == "1":
    print("enable tracing")
    compiler_directives = {
        "linetrace": "True",
        "distutils": "define_macros=CYTHON_TRACE=1",
    }
else:
    compiler_directives = {}


setup(
    name="bencode2",
    version="0.0.7",
    description="bencode serialize/deserialize library",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    author="trim21",
    author_email="trim21.me@gmail.com",
    url="https://github.com/trim21/py-bencode",
    package_dir={"bencode2": "bencode2"},
    packages=["bencode2"],
    package_data={"bencode2": ["py.typed"]},
    include_package_data=True,
    ext_modules=cythonize(
        "bencode2/**/*.pyx",
        compiler_directives={"language_level": "3", **compiler_directives},
    ),
)
