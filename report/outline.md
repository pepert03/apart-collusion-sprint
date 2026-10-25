# Report outline (superseded by report/report.md; current rule: 4-8 pages on the official template, excluding references/appendices)

Target the judging criteria: rigour, novelty/interest, communication.
Word budget below is planning only; the submitted report follows the template's page limit.

## 1. Title + abstract (~120)

One paragraph: question, setup, headline result, one-line takeaway.

## 2. Introduction (~200)

- Collusion between AI agents is a deployment risk (pricing-like games).
- Most work is detection (probes, traffic analysis). Prevention is less studied.
- This sprint: replicate the emergent-collusion baseline, then test which
  cheap interventions actually suppress collusion vs push it underground.

## 3. Setup (~350)

- Iterated prisoner's dilemma, free-form dialogue between rounds, LLM agents.
- Protocol instruction given to agents (quote it).
- Baseline replication: reward structure conflicting with protocol; collusion
  emerges in ~94% of trajectories in the published result; our replication rate.
- Models used (capability ladder), sessions per condition (20-30), rounds.
- Link to repo; exact commands to reproduce.

## 4. Interventions (~250)

Five between-subjects conditions: control, announced audits, unannounced audits,
outcome penalty, restricted channel. One or two sentences each: what changes
for the agent. Pre-registration link.

## 5. Results (~350)

- Figure 1: collusion rate per condition with 95% bootstrap CIs.
- Figure 2: task reward per condition (does the intervention cost performance?).
- Steganography check: collusion rate among sessions with no overt coordination
  language, blind re-rated.
- Transfer: best intervention on public goods game + second model.

## 6. Discussion and limitations (~250)

- Which interventions worked, which backfired, why.
- Honest limits: pilot scale, two models, one game family, judge-model bias
  in the steganography check, penalty heuristic is crude.

## 7. Conclusion (~80)

Two sentences: the finding, and what a deployment team should take from it.

## References

Excluded from the word count. Cite the baseline paper, NARCBench,
the "Secret Collusion" line, and the audit literature.
