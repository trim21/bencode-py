#!/usr/bin/env bash
set -euo pipefail

# Meson probes the preprocessor with "-E -dM -"; avoid injecting target there
# because zig's cc1 rejects target flags in that mode.
if [[ $# -eq 1 && "$1" == "--version" ]]; then
  exec zig c++ --version
fi

if printf '%s\n' "$@" | grep -q -- '^-E$' && printf '%s\n' "$@" | grep -q -- '^-dM$'; then
  exec zig c++ "$@"
fi

# Meson linker detection calls "-Wl,--version"; skip target injection there too.
if printf '%s\n' "$@" | grep -q -- '^-Wl,--version$'; then
  exec zig c++ "$@"
fi

exec zig c++ -target "x86_64-linux-gnu.2.17" "$@"
