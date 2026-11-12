#!/usr/bin/env bash
# Download the approved CI toolchain into a caller-owned private directory.
set -euo pipefail
: "${1:?private tool directory required}"
python3 - "$1" <<'PY'
import hashlib,pathlib,sys,urllib.request
root=pathlib.Path(sys.argv[1]);path=root/'go.tar.gz'
url='https://go.dev/dl/go1.26.11.linux-amd64.tar.gz'
expected='9849f4e04ee35303714e34fbc3ac8ab44ea3e448a95aa182f91e3b9b79c710ec'
with urllib.request.urlopen(url,timeout=60) as response,path.open('xb') as output:
    while chunk:=response.read(1024*1024): output.write(chunk)
if hashlib.sha256(path.read_bytes()).hexdigest()!=expected: raise SystemExit('Go toolchain checksum mismatch')
PY
tar -xzf "$1/go.tar.gz" -C "$1"
