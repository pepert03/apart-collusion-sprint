#!/usr/bin/env bash
# One-time setup on a new machine: Python deps, Modal login, API key, deploys.
# Secrets never live in git: the Modal token stays in ~/.modal.toml and the
# vLLM API key in .env (both outside version control).
#
#   bash scripts/setup_machine.sh            # interactive: opens the browser once
#   ROTATE_KEY=1 bash scripts/setup_machine.sh   # force a new API key
#
# If you copied .env from the old machine, the existing key is reused and
# nothing is rotated. Otherwise a new key is generated, the Modal secret is
# overwritten and both apps are redeployed (the old machine's .env stops working).
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python}"
"$PY" -m pip install -q -r requirements.txt modal

# 1. Modal login (browser). Skipped if this machine already has a token.
if ! "$PY" -m modal app list >/dev/null 2>&1; then
  echo "== Modal login: a browser window will open (workspace: jridruejotunon)"
  "$PY" -m modal token new
fi

# 2. API key shared by the vLLM servers and the harness.
if [ -f .env ] && grep -q '^LLM_API_KEY=' .env && [ -z "${ROTATE_KEY:-}" ]; then
  echo "== Reusing LLM_API_KEY from .env"
else
  echo "== Generating a new LLM_API_KEY and updating the Modal secret"
  KEY=$("$PY" -c "import secrets; print(secrets.token_urlsafe(32))")
  "$PY" -m modal secret create vllm-api-key VLLM_API_KEY="$KEY" --force >/dev/null
  printf 'LLM_API_KEY=%s\n' "$KEY" > .env
  REDEPLOY=1
fi

# 3. Deploy (or redeploy) both model servers. Idempotent and fast once the
#    image exists; containers only start (and cost money) on the first request.
if [ -n "${REDEPLOY:-}" ] || ! "$PY" -m modal app list 2>/dev/null | grep -q collusion-qwen3-8b; then
  export PYTHONIOENCODING=utf-8 PYTHONUTF8=1
  MODEL=Qwen/Qwen3-8B      GPU=L40S "$PY" -m modal deploy infra/modal_vllm.py
  MODEL=Qwen/Qwen3-32B-FP8 GPU=H100 "$PY" -m modal deploy infra/modal_vllm.py
fi

echo "== Ready. Next: bash scripts/run_all.sh"
