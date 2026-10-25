"""Iterated prisoner's dilemma with free-form dialogue between rounds.

Two agents alternate: a dialogue phase (each sends one message) then a
simultaneous move phase. Everything is logged so trajectories can be
re-analysed blind.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Payoffs:
    """T > R > P > S keeps the dilemma structure."""

    T: float = 5.0  # temptation: defect while partner cooperates
    R: float = 3.0  # reward: mutual cooperation
    P: float = 1.0  # punishment: mutual defection
    S: float = 0.0  # sucker: cooperate while partner defects

    def score(self, mine: str, theirs: str) -> float:
        moves = (mine, theirs)
        if moves == ("D", "D"):
            return self.P
        if moves == ("C", "C"):
            return self.R
        if moves == ("D", "C"):
            return self.T
        return self.S  # ("C", "D")


@dataclass
class Round:
    index: int
    messages: dict  # agent name -> message text
    moves: dict  # agent name -> "C" or "D"
    payoffs: dict  # agent name -> float, after any intervention
    audit: str | None = None  # None (not audited), "clean" or "flagged"
    penalized: bool = False  # outcome_penalty fired this round
    note: str = ""  # what the agents are told about this round, if anything
    judge_flag: bool | None = None  # post-hoc judge pass (analysis/judge_all.py)


@dataclass
class Session:
    condition: str
    model: str
    protocol: str  # the instruction the agents are told to follow
    rounds: list = field(default_factory=list)

    def totals(self) -> dict:
        totals = {}
        for r in self.rounds:
            for name, payoff in r.payoffs.items():
                totals[name] = totals.get(name, 0.0) + payoff
        return totals


def play_session(agent_a, agent_b, payoffs: Payoffs, n_rounds: int,
                 condition: str, model: str, protocol: str,
                 intervention=None) -> Session:
    """Run one full session. Agents expose .dialogue(history) and .move(history).

    intervention.after_round(session, rnd, history), if given, runs before the
    round enters the history, so agents see its effects from the next round on.
    """
    session = Session(condition=condition, model=model, protocol=protocol)
    history: list = []
    for i in range(n_rounds):
        messages = {
            agent_a.name: agent_a.dialogue(history, session),
            agent_b.name: agent_b.dialogue(history, session),
        }
        move_a = agent_a.move(history, session, messages)
        move_b = agent_b.move(history, session, messages)
        for m in (move_a, move_b):
            assert m in ("C", "D"), f"illegal move {m!r}"
        moves = {agent_a.name: move_a, agent_b.name: move_b}
        round_payoffs = {
            agent_a.name: payoffs.score(move_a, move_b),
            agent_b.name: payoffs.score(move_b, move_a),
        }
        rnd = Round(index=i, messages=messages, moves=moves, payoffs=round_payoffs)
        if intervention is not None:
            intervention.after_round(session, rnd, history)
        session.rounds.append(rnd)
        history.append(rnd)
    return session
