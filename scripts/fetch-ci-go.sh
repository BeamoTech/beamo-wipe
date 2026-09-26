#!/usr/bin/env bash
# Download the approved CI toolchain into a caller-owned private directory.
set -euo pipefail
: "${1:?private tool directory required}"
python3 - "$1" <<'PY'
import hashlib,pathlib,sys,urllib.request
root=pathlib.Path(sys.argv[1]);path=root/'go.tar.gz'
url='https://go.dev/dl/go1.26.8.linux-amd64.tar.gz'
expected='d0f743b33e8d8945e6b1f432edd15785c70507121d6e2a723b21285eddf8b57b'
with urllib.request.urlopen(url,timeout=60) as response,path.open('xb') as output:
    while chunk:=response.read(1024*1024): output.write(chunk)
if hashlib.sha256(path.read_bytes()).hexdigest()!=expected: raise SystemExit('Go toolchain checksum mismatch')
PY
tar -xzf "$1/go.tar.gz" -C "$1"
