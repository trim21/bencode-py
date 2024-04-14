from setuptools import setup

from Cython.Build import cythonize

setup(
    url='https://github.com/trim21/py-bencode',
    package_dir={'bencode2': 'bencode2'},
    packages=['bencode2'],
    package_data={'bencode2': ['py.typed']},
    include_package_data=True,
    ext_modules=cythonize(
        "bencode2/**/*.pyx",
        compiler_directives={"language_level": "3"},
    ),
)
