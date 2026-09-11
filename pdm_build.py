"""Build hook adding the optional C++ extension to the wheel.

The wheel itself is built by pdm-backend, this hook only compiles the
extension with meson and adds it to the wheel. Setting
``BENCODE2_PURE_PYTHON=1``, or building on a non-CPython interpreter, skips
the extension and produces a ``py3-none-any`` wheel.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdm.backend.hooks.base import Context

_EXTENSION_NAME = "__bencode"
_LIMITED_API_SETTING = "--py-limited-api"
_EXTENSION_SUFFIXES = (".so", ".pyd")


def _extension_enabled(context: Context) -> bool:
    # editable installs and sdists never contain a compiled extension
    if context.target != "wheel":
        return False
    if sys.implementation.name != "cpython":
        return False
    return os.environ.get("BENCODE2_PURE_PYTHON") != "1"


def pdm_build_initialize(context: Context) -> None:
    if _extension_enabled(context):
        # a wheel containing a compiled extension is platform specific
        context.config.build_config["is-purelib"] = False


def pdm_build_update_files(context: Context, files: dict[str, Path]) -> None:
    if not _extension_enabled(context):
        return
    extension = _compile_extension(context)
    files[f"bencode2/{extension.name}"] = extension


def _compile_extension(context: Context) -> Path:
    build_dir = Path(tempfile.mkdtemp(prefix="bencode2-meson-"))
    try:
        meson_args: list[str] = []
        if _LIMITED_API_SETTING in context.config_settings:
            # meson.build only builds for the limited API when this option is enabled
            meson_args.append("-Dpython.allow_limited_api=true")
        _run_meson(["setup", str(build_dir), *meson_args], context)
        _run_meson(["compile", "-C", str(build_dir)], context)
        extension = _find_extension(build_dir)

        # not context.ensure_build_dir(): its .gitignore would end up in the wheel
        target = context.build_dir / "bencode2" / extension.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extension, target)
        return target
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def _run_meson(args: list[str], context: Context) -> None:
    subprocess.run(["meson", *args], cwd=context.root, check=True)


def _find_extension(build_dir: Path) -> Path:
    found = [
        path
        for path in build_dir.glob(f"**/{_EXTENSION_NAME}.*")
        if path.is_file() and path.name.endswith(_EXTENSION_SUFFIXES)
    ]
    if len(found) != 1:
        raise RuntimeError(f"expected exactly one built extension, found {found}")
    return found[0]
