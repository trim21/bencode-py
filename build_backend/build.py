"""
Build backend to build a meson-project when needed
"""

import os
import sys

pure_py = (sys.implementation.name != "cython") or (
    os.environ.get("BENCODE2_PURE_PYTHON") == "1"
)

if pure_py:
    import flit_core.buildapi

    build_wheel = flit_core.buildapi.build_wheel
    build_sdist = flit_core.buildapi.build_sdist
else:
    import mesonpy

    build_wheel = mesonpy.build_wheel
    build_sdist = mesonpy.build_sdist
