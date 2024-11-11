import os
import sys
from glob import glob

from pybind11.setup_helpers import Pybind11Extension, build_ext
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
    macro = [("FMT_HEADER_ONLY", "")]

    extra_compile_args = None
    # if os.environ.get("BENCODE_CPP_DEBUG") == "1":
    # macro.append(("BENCODE_CPP_DEBUG", "1"))
    if sys.platform == "win32":
        extra_compile_args = ["/utf-8", "/Zc:__cplusplus"]

    module = Pybind11Extension(
        "bencode2.__bencode",
        sources=sorted(glob("./src/bencode2/*.cpp")),
        include_dirs=[
            "./src/bencode2",
            "./vendor/fmt/include",
            "./vendor/small_vector/source/include",
        ],
        define_macros=macro,
        extra_compile_args=extra_compile_args,
        cxx_std=17,
    )

    setup(
        ext_modules=[module],
        cmdclass={"build_ext": build_ext},
    )
