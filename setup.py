from setuptools import setup

from Cython.Build import cythonize


def get_readme():
    """Load README.rst for display on PyPI."""
    with open('readme.md') as f:
        return f.read()


setup(
    name='bencode2',
    version='0.0.2',
    description='bencode serialize/deserialize library',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    author='trim21',
    author_email='trim21.me@gmail.com',
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
