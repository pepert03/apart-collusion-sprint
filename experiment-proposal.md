# Breaking emergent collusion: which interventions actually work?

One-page experiment pitch for the Apart Research AI Collusion Sprint (Oct 23-25, 2026).
Angle: RL / training side. Shareable in #projects-teams or with a forming team.

## The question

Most collusion work is detection: probes on activations (NARCBench, arXiv:2604.01151, hit AUROC 1.00 in-distribution) or black-box analysis of message traffic.
Less studied is prevention: which cheap interventions actually suppress collusion,
and which just push it underground into steganographic channels? We test that
directly, in a weekend-sized experiment.

## Setup

Iterated prisoner's dilemma with free-form dialogue between rounds, played by LLM
agents. Published baseline (Emergent Collusion in Long-Horizon LLM Agent Interaction, arXiv:2609.24967, Sep 2026): collusion emerges in 94% of trajectories
when the reward structure conflicts with the protocol, and more capable models
collude earlier. Step one of the weekend is reproducing that baseline with open
models, so we can also inspect internals if time allows. Step two adds the
interventions.

## Interventions (between-subjects)

1. Control: no intervention, free dialogue.
2. Announced audits: agents are told a random sample of their dialogue will be reviewed.
3. Unannounced audits: same sampling, agents are not told.
4. Outcome penalty: suspiciously correlated payoffs trigger a penalty. Tests whether
   punishment breaks coordination or merely hides it.
5. Restricted channel: no free-form dialogue, only structured moves.

## Metrics

- Collusion rate per condition (sustained coordinated play against the protocol).
- Task reward per condition: does the intervention cost the agents real performance?
- Steganography check: does collusion persist without overt coordination language?
  Blind re-rating of a dialogue sample, inspired by the "Secret Collusion" line of work.
- Transfer: the best intervention re-tested on a second game (public goods) and a
  second model, to check it is not a one-game artifact.

## Weekend scope

Pilot scale: 2 models, 20 to 30 sessions per condition, simple stats with bootstrap
CIs. Deliverables: public repo with the harness, a short writeup, and the video
if the submission format asks for one. Other participants are already running
pilot experiments ahead of the sprint, so arriving with a concrete plan is the
norm, not the exception.

## Team

Jose: MSc student in AI (Madrid), into RL. I would own experiment design and
analysis. Looking for: one person on harness/infra, one on eval and writeup.
Hub teams get $250 in Modal credits, which should cover the API bill for a pilot
this size.

## Open questions for the team

- Which open models (capability ladder matters: stronger models collude earlier)?
- Exact operational definition of "collusion" for the PD payoff matrix we use.
- Whether to pre-register the analysis plan before running conditions.
