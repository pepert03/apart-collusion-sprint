# Breaking emergent collusion: which interventions actually work?

Apart Research AI Collusion Sprint, Oct 23-25, 2026. LLM agents play an
iterated prisoner's dilemma with free-form dialogue, under a protocol that
forbids coordinating. We test which cheap interventions (announced and
unannounced audits, an outcome penalty, removing the dialogue channel)
suppress collusion, and which only push it underground.

- Pitch: `experiment-proposal.md`
- Analysis plan, **frozen Oct 21 before the confirmatory run**: `preregistration.md`
- Submitted report: `report/report.pdf` (built from `report/report.html`, the official template; text also in `report/report.md`)

## Status

- [x] Harness, interventions, metrics, analysis; smoke-tested end to end.
- [x] Pilot: 3 sessions x 5 conditions x 2 models, in `data/pilot/` (excluded
      from confirmatory analysis; it shaped the protocol and metric, see the
      preregistration).
- [x] Confirmatory run (Oct 25): 250 sessions, 0 dropped. Trajectories in
      `data/qwen3-8b/`, `data/qwen3-32b/`; full table in `data/results.txt`.
- [x] Report: `report/report.md` (Figure 1: `report/fig1.png`; appendices: Limitations, Dual-Use, full results table).
- [ ] Submission. **Due Sun Oct 25, 23:59 AoE (Mon Oct 26, 12:59 CET)**: report 4-8 pages
      on the official template plus this repo **public**.

## Provenance

The harness, pilot, and preregistration predate the sprint (preregistration frozen Oct 21, 2026); the confirmatory run, judge pass, analysis, figure, and report were produced during the sprint (Oct 23-25, 2026).

**Headline (Qwen3-32B):** announced audits cut overt collusion from 96% to 4%
of sessions while sustained (C,C) stayed at 96% and reward was unchanged:
agents switched to messages like "I will act independently as required by the
protocol". Only the outcome penalty changed behaviour. See the report.

## Setting up on a new machine

Needs Python 3.11+, git and bash (Git Bash on Windows).

```bash
git clone git@github.com:pepert03/apart-collusion-sprint.git
cd apart-collusion-sprint
bash scripts/setup_machine.sh
```

The script installs dependencies, logs into Modal (opens the browser once:
log in with the account that owns the `jridruejotunon` workspace), makes sure
the API key exists and deploys both model servers.

**Secrets are not in the repo, on purpose** (it will be public):

| Secret | Where it lives | How to get it on a new machine |
| --- | --- | --- |
| Modal token | `~/.modal.toml` | `modal token new` (the script runs it) |
| vLLM API key | `.env` (`LLM_API_KEY`) + Modal secret `vllm-api-key` | Copy `.env` from the old machine over a private channel, **or** let the script generate a new one (it overwrites the Modal secret and redeploys; the old machine's `.env` then stops working) |

Template: `.env.example`. The servers reject requests without the key (HTTP 401).

## Infrastructure

Two vLLM servers on Modal (`infra/modal_vllm.py`), OpenAI-compatible:

| Model | GPU | URL (`/v1`) |
| --- | --- | --- |
| Qwen/Qwen3-8B | L40S | `https://jridruejotunon--collusion-qwen3-8b-serve.us-east.modal.run/v1` |
| Qwen/Qwen3-32B-FP8 (also the judge) | H100 | `https://jridruejotunon--collusion-qwen3-32b-fp8-serve.us-east.modal.run/v1` |

They scale to zero after 5 idle minutes, so credits are only spent while
sessions run. Cold start: ~2 min (8B), ~7 min (32B). Credits, usage and the
spend limit are under Settings -> Usage & Billing on modal.com.

`OpenAICompatibleBackend` (`src/agents.py`) is stdlib only, so Ollama or a
hosted endpoint (OpenRouter, Together, ...) work the same way via `--base-url`.

## Running

Smoke test, no model needed (random play, random judge):

```bash
pip install -r requirements.txt
for c in control announced_audit unannounced_audit outcome_penalty restricted_channel; do
  python src/run.py --condition $c --sessions 4 --out data/smoke/$c.jsonl
done
python analysis/judge_all.py --files data/smoke/*.jsonl --judge-model random-stub
python analysis/bootstrap.py --files data/smoke/*.judged.jsonl
```

Reproduce the report numbers and figure from the committed data (no model needed):

```bash
python analysis/bootstrap.py --files data/qwen3-*/*.judged.jsonl
python analysis/explore.py   --files data/qwen3-*/*.judged.jsonl
python analysis/plot.py      --files data/qwen3-*/*.judged.jsonl --out report/fig1.png
```

Confirmatory run (2 models x 5 conditions x 25 sessions x 20 rounds, then the
judge pass and the analysis). Resumable: re-running skips finished sessions.

```bash
bash scripts/run_all.sh                          # -> data/results.txt
SESSIONS=3 OUT=data/pilot2 bash scripts/run_all.sh   # quick pilot
```

Single condition by hand:

```bash
set -a; . ./.env; set +a
python src/run.py --condition control --sessions 25 --model Qwen/Qwen3-8B \
  --base-url https://jridruejotunon--collusion-qwen3-8b-serve.us-east.modal.run/v1 \
  --judge-model Qwen/Qwen3-32B-FP8 \
  --judge-base-url https://jridruejotunon--collusion-qwen3-32b-fp8-serve.us-east.modal.run/v1 \
  --no-think --workers 8 --out data/qwen3-8b/control.jsonl
```

Useful flags: `--workers` (parallel sessions), `--resume`, `--no-think`
(skip Qwen3 reasoning traces). On a persistent API failure the run stops
instead of writing fake output.

## How it works

- `src/game.py`: each round both agents send one message, then move C/D
  simultaneously. Everything is logged (messages, moves, payoffs, audits).
- `src/agents.py`: prompts, message cleaning (<= 40 words, 400 chars),
  robust C/D parsing.
- `src/interventions.py`: the 5 conditions. Audits (20% of rounds, judge
  zeroes the round's payoffs if it finds coordination) and the outcome
  penalty (-2 each from the 3rd consecutive (C,C)) act **during** play.
- `analysis/judge_all.py`: the fixed judge (Qwen3-32B-FP8, temperature 0)
  rates every round's messages post hoc -> `*.judged.jsonl`.
- `src/metrics.py` + `analysis/bootstrap.py`: overt collusion (sustained (C,C)
  plus explicit coordination), concealment (sustained (C,C), nothing flagged),
  sustained (C,C), reward; 95% bootstrap CIs and differences vs control and
  vs the restricted-channel baseline.

## Layout

```
src/        game, agents, interventions, metrics, run.py (CLI)
analysis/   judge_all.py, bootstrap.py, explore.py, plot.py
infra/      modal_vllm.py (model servers)
scripts/    setup_machine.sh, run_all.sh
data/        pilot/ and confirmatory trajectories (raw + judged), results.txt
report/     report.pdf (submitted), report.html (its source), report.md, fig1.svg/.png, fonts/
```
