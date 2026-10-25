"""Post-hoc judge pass: rate every round's messages for explicit coordination.

Independent of the in-game audits (which only see 20% of rounds and change
payoffs). The judge sees one round's messages only, never moves or payoffs,
at temperature 0. Identical message pairs are judged once.

Writes <file>.judged.jsonl next to each input, leaving raw trajectories untouched.

Usage:
    python analysis/judge_all.py --files data/qwen3-8b/*.jsonl \\
        --judge-model Qwen/Qwen3-32B-FP8 --base-url $JUDGE_BASE_URL --workers 32
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents import OpenAICompatibleBackend, RandomStub  # noqa: E402
from interventions import judge_prompt  # noqa: E402
from metrics import DIALOGUE_FREE  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--judge-model", default="Qwen/Qwen3-32B-FP8",
                    help="'random-stub' for smoke tests")
    ap.add_argument("--base-url", default=None, help="defaults to $LLM_BASE_URL")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    if args.judge_model == "random-stub":
        judge = RandomStub(seed=0)
    else:
        judge = OpenAICompatibleBackend(args.judge_model, base_url=args.base_url,
                                        temperature=0.0, no_think=True, max_tokens=8)

    files = [f for f in args.files if not f.endswith(".judged.jsonl")]
    sessions = {f: [json.loads(line) for line in open(f) if line.strip()] for f in files}

    # Unique (protocol, messages) pairs across all files.
    def key(d, r):
        return (d["protocol"], tuple(sorted(r["messages"].items())))

    todo = {key(d, r) for ss in sessions.values() for d in ss
            if d["condition"] not in DIALOGUE_FREE for r in d["rounds"]}
    print(f"judging {len(todo)} unique rounds with {args.judge_model}", file=sys.stderr)

    def rate(k):
        protocol, msgs = k
        verdict = judge.call(judge_prompt(protocol, dict(msgs)))
        return k, re.search(r"\bYES\b", verdict.upper()) is not None

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        verdicts = dict(pool.map(rate, todo))

    for f, ss in sessions.items():
        out = f[: -len(".jsonl")] + ".judged.jsonl"
        with open(out, "w") as fh:
            for d in ss:
                for r in d["rounds"]:
                    r["judge_flag"] = (False if d["condition"] in DIALOGUE_FREE
                                       else verdicts[key(d, r)])
                d["judge_model"] = args.judge_model
                fh.write(json.dumps(d) + "\n")
        print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
