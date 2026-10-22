#!/usr/bin/env bash
# Disposable unprivileged development container; no devices or Docker socket.
set -euo pipefail
if [ "$#" -eq 0 ]; then set -- bash; fi
docker_args=(run --rm --init -i --cap-drop=ALL --security-opt=no-new-privileges
  --user "$(id -u):$(id -g)"
  --mount 'type=bind,src=/workspace/beamo-wipe,dst=/workspace/beamo-wipe'
  --mount 'type=bind,src=/workspace/beamo-tools,dst=/workspace/beamo-tools'
  --mount 'type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/proxy-bundle.pem,readonly'
  -e HOME=/home/beamo -e PIP_CERT=/run/proxy-bundle.pem
  -e SSL_CERT_FILE=/run/proxy-bundle.pem -e REQUESTS_CA_BUNDLE=/run/proxy-bundle.pem
  -e NODE_EXTRA_CA_CERTS=/run/proxy-bundle.pem
  -e GOCACHE=/workspace/beamo-tools/gocache -e GOPATH=/workspace/beamo-tools/gopath
  -e BEAMO_GO_BIN=go
  -e XDG_CACHE_HOME=/workspace/beamo-tools/cache
  -e PLAYWRIGHT_BROWSERS_PATH=/workspace/beamo-tools/playwright
  -e PATH=/workspace/beamo-wipe/.venv-linux/bin:/opt/beamo-venv/bin:/opt/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  --workdir /workspace/beamo-wipe)
if [ -t 0 ] && [ -t 1 ]; then docker_args+=(-t); fi
exec env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  docker --host=unix:///var/run/docker.sock "${docker_args[@]}" beamo-wipe-dev:20261017 "$@"
