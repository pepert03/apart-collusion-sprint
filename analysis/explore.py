"""Exploratory (not confirmatory, see preregistration.md):

1. Share of rounds the judge flags as explicit coordination, per condition.
2. Reaction to audits: P(both cooperate next round) after a flagged vs a
   clean audit, in the two audit conditions.

Usage:
    python analysis/explore.py --files data/*/*.judged.jsonl
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from bootstrap import ORDER, load  # noqa: E402


def both_c(r) -> bool:
    return all(m == "C" for m in r.moves.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", required=True)
    args = ap.parse_args()

    groups = defaultdict(list)
    for path in args.files:
        for s in load(path):
            groups[(s.model, s.condition)].append(s)

    for model in sorted({m for m, _ in groups}):
        print(f"\n=== {model} ===")
        print("flagged-round share (judge pass):")
        for c in ORDER:
            if (model, c) not in groups or c == "restricted_channel":
                continue
            rounds = [r for s in groups[(model, c)] for r in s.rounds]
            print(f"  {c:18} {sum(r.judge_flag for r in rounds) / len(rounds):.3f}"
                  f"  ({len(rounds)} rounds)")
        print("P(C,C next round | audit result):")
        for c in ("announced_audit", "unannounced_audit"):
            nxt = defaultdict(list)
            for s in groups.get((model, c), []):
                for r, r_next in zip(s.rounds, s.rounds[1:]):
                    if r.audit:
                        nxt[r.audit].append(both_c(r_next))
            cells = "  ".join(f"after {k}: {sum(v) / len(v):.2f} (n={len(v)})"
                              for k, v in sorted(nxt.items()))
            print(f"  {c:18} {cells}")


if __name__ == "__main__":
    main()
