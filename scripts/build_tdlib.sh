#!/usr/bin/env bash
# Build libtdjson.so from the official TDLib source and vendor it into ./lib/.
#
# This compiles only the `tdjson` target (the JSON interface we use). Requires:
#   g++/clang, cmake >= 3.10, gperf, libssl-dev, zlib1g-dev
#
# Usage: scripts/build_tdlib.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${TDLIB_BUILD_DIR:-/tmp/tdlib-build}"

echo ">> Installing build dependencies (needs sudo/root)..."
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq || true
    apt-get install -y -qq g++ cmake gperf libssl-dev zlib1g-dev git || true
fi

mkdir -p "$WORK"
if [ ! -d "$WORK/td" ]; then
    echo ">> Cloning TDLib..."
    git clone --depth 1 https://github.com/tdlib/td.git "$WORK/td"
fi

echo ">> Configuring..."
mkdir -p "$WORK/td/build"
cd "$WORK/td/build"
cmake -DCMAKE_BUILD_TYPE=Release -DTD_ENABLE_LTO=OFF ..

echo ">> Building tdjson (this takes a while)..."
cmake --build . --target tdjson -- -j"$(nproc)"

echo ">> Vendoring libtdjson into $REPO_ROOT/lib/ ..."
mkdir -p "$REPO_ROOT/lib"
cp -v "$(find "$WORK/td/build" -name 'libtdjson.so*' | head -1)" "$REPO_ROOT/lib/libtdjson.so"

echo ">> Done. libtdjson.so is in $REPO_ROOT/lib/"
