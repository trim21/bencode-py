#!/usr/bin/env bash
set -euo pipefail

# Shim to inject Zig target when used as the C++ compiler.
target="${ZIG_TARGET:-x86_64-linux-gnu.2.17}"

if [[ $# -eq 1 && "$1" == "--version" ]]; then
  exec zig c++ --version
fi

exec zig c++ --target "${target}" "$@"
