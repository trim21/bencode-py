"""
Build backend to build a meson-project when needed
"""

import os
import sys

pure_py = (sys.implementation.name != "cython") or (
    os.environ.get("BENCODE2_PURE_PYTHON") == "1"
)

if pure_py:
    from flit_core.buildapi import *  # noqa: F403

else:
    from mesonpy import *  # noqa: F403
