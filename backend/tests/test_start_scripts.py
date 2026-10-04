"""Exercise the Linux launcher's build gate with isolated dependency stand-ins."""
import os
from pathlib import Path
import shutil
import subprocess
import time
import pytest

ROOT = Path(__file__).resolve().parents[2]
BASH = shutil.which("bash")

@pytest.fixture
def launcher(tmp_path):
    if not BASH:
        pytest.skip("bash not installed")
    root = tmp_path / "project with spaces"
    root.mkdir()
    shutil.copyfile(ROOT / "start.sh", root / "start.sh")
    for folder in ("backend/.venv/bin", "frontend/src", "frontend/public", "frontend/scripts", "frontend/node_modules", "frontend/dist/vad", "test-bin"):
        (root / folder).mkdir(parents=True)
    (root / "backend/.venv/bin/python").write_text('#!/usr/bin/env bash\nif [[ "$1" == "-m" ]]; then printf "LAUNCHED:%s\\n" "$2"; fi\n')
    (root / "test-bin/node").write_text('#!/usr/bin/env bash\nexit 0\n')
    (root / "test-bin/npm").write_text('#!/usr/bin/env bash\nprintf "BUILD\\n"\nexit "${MOCK_BUILD_EXIT:-0}"\n')
    for executable in (root / "backend/.venv/bin/python", root / "test-bin/node", root / "test-bin/npm"):
        executable.chmod(0o755)
    for name in ("index.html", "vad/silero_vad_v5.onnx", "vad/vad.worklet.bundle.min.js", "vad/ort-wasm-test.wasm", "vad/ort-wasm-test.mjs"):
        (root / "frontend/dist" / name).write_text("fixture")
    for name in ("package.json", "package-lock.json", "index.html", "vite.config.ts", "tsconfig.json", "src/App.tsx"):
        path = root / "frontend" / name
        path.write_text("fixture")
        os.utime(path, (time.time() - 60, time.time() - 60))
    (root / "run-test.sh").write_text('#!/usr/bin/env bash\ncd -- "$(dirname -- "$0")"\nexport PATH="$PWD/test-bin:$PATH"\nbash ./start.sh\n')
    def run(fail=False):
        env = {**os.environ, "MOCK_BUILD_EXIT": "9" if fail else "0"}
        return subprocess.run([BASH, str(root / "run-test.sh")], env=env, capture_output=True, text=True, timeout=20)
    return root, run

def test_launcher_reuses_current_build_and_rebuilds_newer_source(launcher):
    root, run = launcher
    first = run()
    assert first.returncode == 0, first.stderr
    assert "Frontend build is current." in first.stdout and "LAUNCHED:app.main" in first.stdout
    future = time.time() + 5
    os.utime(root / "frontend/src/App.tsx", (future, future))
    second = run()
    assert second.returncode == 0, second.stderr
    assert "BUILD" in second.stdout and "LAUNCHED:app.main" in second.stdout

def test_launcher_stops_after_failed_build(launcher):
    root, run = launcher
    (root / "frontend/dist/index.html").unlink()
    result = run(fail=True)
    assert result.returncode == 9
    assert "BUILD" in result.stdout and "LAUNCHED:" not in result.stdout

def test_launcher_refuses_missing_dependencies(launcher):
    root, run = launcher
    (root / "backend/.venv/bin/python").unlink()
    result = run()
    assert result.returncode != 0 and "Missing backend/.venv" in result.stderr
