import os
from setuptools import setup, Extension

from Cython.Build import cythonize


def get_readme():
    with open("readme.md", encoding="utf-8") as f:
        return f.read()


if os.environ.get("COV") == "1":
    define_macros = [("CYTHON_TRACE", "1")]
    compiler_directives = {
        "linetrace": "True",
    }
else:
    define_macros = None
    compiler_directives = {}

extensions = [
    # Everything but primes.pyx is included here.
    Extension("*", ["**/*.pyx"], define_macros=define_macros)
]

setup(
    name="bencode2",
    version="0.0.11",
    description="bencode serialize/deserialize library",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    author="trim21",
    author_email="trim21.me@gmail.com",
    url="https://github.com/trim21/py-bencode",
    python_requires=">=3.8",
    package_dir={"bencode2": "bencode2"},
    packages=["bencode2"],
    package_data={"bencode2": ["py.typed"]},
    include_package_data=True,
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3", **compiler_directives},
    ),
)
