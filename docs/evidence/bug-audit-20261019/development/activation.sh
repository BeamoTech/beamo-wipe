# Source this file for development in the managed executor.
export BEAMO_GO_BIN=go
export GOTOOLCHAIN=local
export GOCACHE=/workspace/beamo-tools/gocache
export GOPATH=/workspace/beamo-tools/gopath
export PIP_CACHE_DIR=/workspace/beamo-tools/pip-cache
export UV_CACHE_DIR=/workspace/beamo-tools/uv-cache
export XDG_CACHE_HOME=/workspace/beamo-tools/cache
export PLAYWRIGHT_BROWSERS_PATH=/workspace/beamo-tools/playwright
export PATH="/workspace/beamo-wipe/.venv-linux/bin:/workspace/beamo-tools/go/bin:/workspace/beamo-tools/x11/usr/bin:/workspace/beamo-tools/sysroot/usr/bin:/workspace/beamo-tools/sysroot/usr/sbin:$PATH"
export LD_LIBRARY_PATH="/workspace/beamo-tools/sysroot/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GI_TYPELIB_PATH="/workspace/beamo-tools/sysroot/usr/lib/x86_64-linux-gnu/girepository-1.0${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
export XDG_DATA_DIRS="/workspace/beamo-tools/sysroot/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export PYTHONPATH="/workspace/beamo-wipe/src:/workspace/beamo-tools/sysroot/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
