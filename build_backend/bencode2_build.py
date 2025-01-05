"""
Build backend to build a meson-project when needed
"""

import os
import sys

pure_py = (sys.implementation.name != "cpython") or (
    os.environ.get("BENCODE2_PURE_PYTHON") == "1"
)

if pure_py:
    import  flit_core.buildapi as build_api

else:
    import  mesonpy as build_api

__all__ = ['build_api']
