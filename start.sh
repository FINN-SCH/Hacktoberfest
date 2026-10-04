#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/backend/.venv/bin/python"
FRONTEND="$ROOT/frontend"
INDEX="$FRONTEND/dist/index.html"

if [[ ! -x "$PYTHON" ]]; then
  printf '%s\n' 'Missing backend/.venv. Follow SETUP_GUIDE.md step 3.' >&2
  exit 1
fi
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  printf '%s\n' 'Missing frontend/node_modules. Run: cd frontend && npm ci' >&2
  exit 1
fi
command -v node >/dev/null || { printf '%s\n' 'Node.js 22.11+ is required.' >&2; exit 1; }
command -v npm >/dev/null || { printf '%s\n' 'npm is required.' >&2; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(a<22||(a===22&&b<11)){console.error("Node.js 22.11+ is required.");process.exit(1)}'
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ is required"'

needs_build=0
if [[ ! -f "$INDEX" || ! -f "$FRONTEND/dist/vad/silero_vad_v5.onnx" || ! -f "$FRONTEND/dist/vad/vad.worklet.bundle.min.js" ]] ||
   ! compgen -G "$FRONTEND/dist/vad/ort-wasm*.wasm" >/dev/null ||
   ! compgen -G "$FRONTEND/dist/vad/ort-wasm*.mjs" >/dev/null; then
  needs_build=1
elif find "$FRONTEND/src" "$FRONTEND/public" "$FRONTEND/scripts" -type f -newer "$INDEX" -print -quit | grep -q .; then
  needs_build=1
else
  for input in package.json package-lock.json index.html vite.config.ts tsconfig.json; do
    if [[ "$FRONTEND/$input" -nt "$INDEX" ]]; then needs_build=1; break; fi
  done
fi
if [[ "$needs_build" == 1 ]]; then
  printf '%s\n' 'Building frontend (missing or stale dist)...'
  (cd "$FRONTEND" && npm run build)
else
  printf '%s\n' 'Frontend build is current.'
fi
cd "$ROOT/backend"
"$PYTHON" -c 'from app.config import Settings; s=Settings(); print(f"Tutor URL: http://{s.host}:{s.port} (Ctrl+C to stop)")'
exec "$PYTHON" -m app.main
