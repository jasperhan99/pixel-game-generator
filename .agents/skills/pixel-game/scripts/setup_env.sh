#!/usr/bin/env bash
# Create (or repair) a uv-managed Pyxel project directory.
#   bash setup_env.sh <project_dir>
# Idempotent: safe to re-run. Prints "ENV READY" on success.
set -euo pipefail

PROJECT_DIR="${1:?usage: setup_env.sh <project_dir>}"
PY_VERSION="${PYXEL_PY_VERSION:-3.12}"   # pyxel needs >=3.11

log() { printf '[setup] %s\n' "$*"; }

# 1. uv (manages Python + deps). Installing uv is a global change, so we never
#    do it silently: exit 2 and let the agent ask the user.
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv is not installed. Ask the user to install it with ONE of:" >&2
  command -v brew >/dev/null 2>&1 && echo "  brew install uv" >&2
  command -v pipx >/dev/null 2>&1 && echo "  pipx install uv" >&2
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh        # macOS/Linux" >&2
  echo "  powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"   # Windows" >&2
  echo "then re-run this script." >&2
  exit 2
fi
log "uv $(uv --version | awk '{print $2}')"

# 2. project
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
NAME="$(basename "$PWD" | tr '[:upper:]_ ' '[:lower:]--' | tr -cd 'a-z0-9-')"
if [ ! -f pyproject.toml ]; then
  log "initialising uv project '$NAME' (python $PY_VERSION)"
  uv init --bare --no-workspace --name "${NAME:-pixel-game}" --python "$PY_VERSION" >/dev/null
fi
[ -f .python-version ] || uv python pin "$PY_VERSION" >/dev/null

# 3. dependency
if ! grep -q '"pyxel' pyproject.toml; then
  log "adding pyxel"
  uv add "pyxel>=2.9" >/dev/null
fi
uv sync --quiet

# 4. .gitignore
[ -f .gitignore ] || printf '.venv/\n__pycache__/\nplaytest_out/\n*.pyxapp\n' > .gitignore

# 5. verify
uv run python -c "import pyxel, sys; print(f'[setup] python {sys.version.split()[0]}, pyxel {pyxel.VERSION}')"
echo "ENV READY: $PWD"
