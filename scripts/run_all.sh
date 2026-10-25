#!/usr/bin/env bash
# Confirmatory run: 5 conditions x 2 models x 25 sessions, judge pass, analysis.
# Needs the two Modal apps deployed (infra/modal_vllm.py) and LLM_API_KEY in .env.
# Safe to re-run: --resume skips sessions already on disk.
#
#   bash scripts/run_all.sh                 # everything
#   SESSIONS=3 OUT=data/pilot bash scripts/run_all.sh   # quick pilot
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

WS="${MODAL_WORKSPACE:-jridruejotunon}"
B8="https://${WS}--collusion-qwen3-8b-serve.us-east.modal.run/v1"
B32="https://${WS}--collusion-qwen3-32b-fp8-serve.us-east.modal.run/v1"
JUDGE="Qwen/Qwen3-32B-FP8"
SESSIONS="${SESSIONS:-25}"
OUT="${OUT:-data}"
CONDITIONS="control announced_audit unannounced_audit outcome_penalty restricted_channel"

run_model() {  # $1 model, $2 base url, $3 dir
  for c in $CONDITIONS; do
    python src/run.py --condition "$c" --sessions "$SESSIONS" --rounds 20 \
      --model "$1" --base-url "$2" --judge-model "$JUDGE" --judge-base-url "$B32" \
      --no-think --workers 8 --resume --out "$OUT/$3/$c.jsonl" &
  done
  wait
}

run_model Qwen/Qwen3-8B "$B8" qwen3-8b &
run_model "$JUDGE" "$B32" qwen3-32b &
wait

python analysis/judge_all.py --files "$OUT"/qwen3-8b/*.jsonl "$OUT"/qwen3-32b/*.jsonl \
  --judge-model "$JUDGE" --base-url "$B32" --workers 32
python analysis/bootstrap.py --files "$OUT"/*/*.judged.jsonl | tee "$OUT/results.txt"
