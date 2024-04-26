import glob
import os
import platform

from setuptools import setup


def get_readme():
    with open("readme.md", encoding="utf-8") as f:
        return f.read()


if (
    platform.python_implementation() == "CPython"
    and os.environ.get("BENCODE2_NO_MYPYC") != "1"
):
    # only use mypyc with cpython.
    from mypyc.build import mypycify

    ext_modules = mypycify(glob.glob("bencode2/*.py"))
else:
    ext_modules = None

setup(
    name="bencode2",
    version="0.0.15",
    description="A fast and correct bencode serialize/deserialize library",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    author="trim21",
    author_email="trim21.me@gmail.com",
    url="https://github.com/trim21/bencode-py",
    python_requires=">=3.8",
    package_dir={"bencode2": "bencode2"},
    packages=["bencode2"],
    package_data={"bencode2": ["py.typed"]},
    include_package_data=True,
    ext_modules=ext_modules,
)
