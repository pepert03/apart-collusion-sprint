"""Preregistered analysis: rates per condition with 95% bootstrap CIs, plus
each condition's difference from control and from the restricted-channel
baseline (tacit cooperation without any channel).

Reads the *.judged.jsonl files written by analysis/judge_all.py.

Usage:
    python analysis/bootstrap.py --files data/qwen3-8b/*.judged.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from game import Round, Session  # noqa: E402
from metrics import (  # noqa: E402
    bootstrap_ci,
    bootstrap_diff_ci,
    indicator,
    is_colluding,
    is_concealed,
    mean,
    sustained_cc,
    task_rewards,
)

ORDER = ["control", "announced_audit", "unannounced_audit", "outcome_penalty",
         "restricted_channel"]
OUTCOMES = {
    "collusion": lambda ss: indicator(is_colluding, ss),
    "concealed": lambda ss: indicator(is_concealed, ss),
    "sustained_cc": lambda ss: indicator(sustained_cc, ss),
    "reward": task_rewards,
}


def load(path: str) -> list:
    sessions = []
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            s = Session(condition=d["condition"], model=d["model"],
                        protocol=d["protocol"])
            s.rounds = [Round(**r) for r in d["rounds"]]
            if any(r.judge_flag is None for r in s.rounds):
                sys.exit(f"{path}: unjudged rounds; run analysis/judge_all.py "
                         "and pass the *.judged.jsonl files")
            sessions.append(s)
    return sessions


def fmt(m, ci, digits=3):
    return f"{m:.{digits}f} [{ci[0]:.{digits}f}, {ci[1]:.{digits}f}]"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", required=True)
    args = ap.parse_args()

    groups = defaultdict(list)  # (model, condition) -> sessions
    for path in args.files:
        for s in load(path):
            groups[(s.model, s.condition)].append(s)

    for model in sorted({m for m, _ in groups}):
        conds = [c for c in ORDER if (model, c) in groups]
        print(f"\n=== {model} ===")
        for c in conds:
            ss = groups[(model, c)]
            print(f"{c} (n={len(ss)})")
            for name, f in OUTCOMES.items():
                v = f(ss)
                line = f"  {name:13} {fmt(mean(v), bootstrap_ci(v), 2 if name == 'reward' else 3)}"
                for ref in ("control", "restricted_channel"):
                    if c != ref and (model, ref) in groups:
                        w = f(groups[(model, ref)])
                        line += (f"  | vs {ref.split('_')[0]}: "
                                 f"{mean(v) - mean(w):+.3f} {fmt_ci(bootstrap_diff_ci(v, w))}")
                print(line)


def fmt_ci(ci):
    return f"[{ci[0]:+.3f}, {ci[1]:+.3f}]"


if __name__ == "__main__":
    main()
