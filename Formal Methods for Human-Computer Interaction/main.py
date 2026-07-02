"""Companion code for Chapter 7, "Formal Methods for Human-Computer
Interaction" (Roggenbach et al., *Formal Methods for Software
Engineering*).

The book models human cognition with a CSP extension (PAT) with integer
variables and arrays; most of the actual PAT source listings (Examples
65.3-65.19) were images/formatted code blocks that did not survive
plain-text extraction, so `main.py` is an original Python re-formalization
of the *mathematical* model the chapter gives in prose (Sec. 7.3.3's
precise enabling/performance/closure conditions for a "basic activity"),
not a transcription of the book's PAT listings.

Two things this file demonstrates end to end:

1. A short-term-memory (STM) + closure engine, and the "old ATM" vs.
   "new ATM" case study (Sec. 7.3.3/7.4) -- mechanically *reproducing* the
   chapter's central example of a post-completion error: an interface
   design bug that only emerges from the interaction between closure and
   event ordering, not from either component alone.
2. An LTL check (Sec. 7.5.1) of the functional-correctness and safety
   property schemas the chapter gives, run against simulated traces from
   both interfaces -- reproducing the chapter's own stated result: the
   safety (card-collection) property fails for the old ATM and holds for
   the new one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ===========================================================================
# 1. Short-term memory, basic activities, and closure (Sec. 7.2.1, 7.3.3)
# ===========================================================================


@dataclass(frozen=True)
class BasicActivity:
    """An automatic basic activity (p, R, S, a) from Sec. 7.3.3: on
    perception `perception`, retrieve/remove `retrieve` from STM, perform
    action `action`, then store `store` in STM. If `achieves_goal` is one
    of the currently active goals, performing this activity discharges
    that goal and triggers *closure*: STM is flushed of everything except
    still-unachieved goals."""

    name: str
    perception: Optional[str]
    retrieve: FrozenSet[str]
    store: FrozenSet[str]
    action: Optional[str]
    achieves_goal: Optional[str] = None


def is_enabled(activity: BasicActivity, stm: Set[str], goals: Set[str], perception: str) -> bool:
    """Sec. 7.3.3's three enabling conditions: the perception matches,
    the retrieved items are present in STM, and the stored items are not
    already there (no duplicate storage)."""
    if activity.perception is not None and activity.perception != perception:
        return False
    if not activity.retrieve <= stm:
        return False
    if activity.store & stm:
        return False
    return True


def perform(activity: BasicActivity, stm: Set[str], goals: Set[str]) -> Tuple[Set[str], Set[str], bool]:
    new_stm = (stm - activity.retrieve) | activity.store
    new_goals = set(goals)
    closure = False
    if activity.achieves_goal is not None and activity.achieves_goal in new_goals:
        new_goals.discard(activity.achieves_goal)
        new_stm = set()  # closure: flush all non-goal STM contents
        closure = True
    return new_stm, new_goals, closure


# ===========================================================================
# 2. The ATM case study (Sec. 7.3.3, 7.4): old vs. new interface
# ===========================================================================
#
# Both interfaces run the same four user activities; they differ only in
# *when* the card is returned relative to the cash. That single ordering
# change is enough to create -- or eliminate -- a post-completion error.

ACTIVITIES: Dict[str, BasicActivity] = {
    "cardR": BasicActivity("insertCard", "cardR", frozenset(), frozenset({"collectCard"}), "cardI"),
    "pinR": BasicActivity("enterPin", "pinR", frozenset(), frozenset(), "pinE"),
    "cashD": BasicActivity("collectCash", "cashD", frozenset(), frozenset(), "cashC", achieves_goal="getCash"),
    "cardO": BasicActivity("collectCard", "cardO", frozenset({"collectCard"}), frozenset(), "cardC"),
}

# The interface's own reactive transitions: perception -> next perception,
# once the corresponding activity has performed its action.
OLD_INTERFACE = {"cardR": "pinR", "pinR": "cashD", "cashD": "cardO", "cardO": None}  # cash before card
NEW_INTERFACE = {"cardR": "pinR", "pinR": "cardO", "cardO": "cashD", "cashD": None}  # card before cash


@dataclass
class RunResult:
    events: List[str] = field(default_factory=list)
    stuck_at: Optional[str] = None  # perception at which no activity could fire


def simulate(interface: Dict[str, Optional[str]], max_steps: int = 10) -> RunResult:
    stm: Set[str] = set()
    goals: Set[str] = {"getCash"}
    perception: Optional[str] = "cardR"
    result = RunResult(events=["begin"])

    for _ in range(max_steps):
        if perception is None:
            break
        activity = ACTIVITIES[perception]
        result.events.append(f"perc:{perception}")
        if not is_enabled(activity, stm, goals, perception):
            result.stuck_at = perception
            break
        stm, goals, closure = perform(activity, stm, goals)
        result.events.append(f"act:{activity.action}")
        perception = interface[perception]
    return result


def _demo_atm_closure() -> None:
    print("--- 7.3.3/7.4 ATM: closure and the post-completion error ---")

    old = simulate(OLD_INTERFACE)
    print(f"  old ATM (cash delivered, THEN card returned):")
    print(f"    trace: {old.events}")
    if old.stuck_at:
        print(f"    stuck at perception '{old.stuck_at}': closure (on collecting cash) flushed the")
        print(f"    'collectCard' reminder from STM before the user ever saw the card -- forgotten card!")

    new = simulate(NEW_INTERFACE)
    print(f"  new ATM (card returned, THEN cash delivered):")
    print(f"    trace: {new.events}")
    if new.stuck_at is None:
        print(f"    completes cleanly: the card is collected (consuming the reminder) before")
        print(f"    the cash-collection closure has any reminder left to accidentally flush.")


# ===========================================================================
# 3. LTL verification of the two interfaces (Sec. 7.5.1)
# ===========================================================================


class LTL:
    pass


@dataclass(frozen=True)
class Prop(LTL):
    name: str


@dataclass(frozen=True)
class Not(LTL):
    inner: LTL


@dataclass(frozen=True)
class Implies(LTL):
    left: LTL
    right: LTL


@dataclass(frozen=True)
class Always(LTL):
    inner: LTL


@dataclass(frozen=True)
class Eventually(LTL):
    inner: LTL


@dataclass(frozen=True)
class Until(LTL):
    left: LTL
    right: LTL


Trace = Tuple[str, ...]


def eval_ltl(f: LTL, trace: Trace, i: int) -> bool:
    if isinstance(f, Prop):
        return i < len(trace) and trace[i] == f.name
    if isinstance(f, Not):
        return not eval_ltl(f.inner, trace, i)
    if isinstance(f, Implies):
        return (not eval_ltl(f.left, trace, i)) or eval_ltl(f.right, trace, i)
    if isinstance(f, Always):
        return all(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    if isinstance(f, Eventually):
        return any(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    if isinstance(f, Until):
        for j in range(i, len(trace)):
            if eval_ltl(f.right, trace, j):
                return all(eval_ltl(f.left, trace, k) for k in range(i, j))
        return False
    raise TypeError(f"unknown LTL node: {f!r}")


def check(f: LTL, trace: List[str]) -> bool:
    return eval_ltl(f, tuple(trace), 0)


def _demo_ltl_verification() -> None:
    print("--- 7.5.1 Model checking: functional correctness and safety ---")

    # "if the user selects cash [i.e. the task begins], the goal is
    # eventually achieved" -- Example 65.17's functional-correctness idea,
    # simplified to this chapter's single-goal ATM.
    functional = Always(Implies(Prop("begin"), Eventually(Prop("act:cashC"))))

    # "no new session begins before the card is collected, once the
    # interface has shown it" -- Example 65.18's safety property, using
    # #assert system |= [] (internal -> (!begin U return)) with
    # internal = card shown (perc:cardO), return = card collected (act:cardC).
    safety = Always(Implies(Prop("perc:cardO"), Until(Not(Prop("begin")), Prop("act:cardC"))))

    for label, interface in [("old ATM", OLD_INTERFACE), ("new ATM", NEW_INTERFACE)]:
        trace = simulate(interface).events
        print(f"  {label}: functional correctness holds? {check(functional, trace)}"
              f"   safety (card collected) holds? {check(safety, trace)}")


# ===========================================================================
# 4. Task-failure decomposition: soundness and completeness (Sec. 7.5.2)
# ===========================================================================
#
# A small, original illustration of the chapter's methodology -- not a
# transcription of the (informal, qualitative) ATC example -- built so the
# soundness/completeness distinction can be checked mechanically:
# a decomposition F = P1 v P2 v ... is *sound* if each Pi implies F, and
# *complete* if F implies P1 v P2 v ... v Pn (nothing causes F that isn't
# covered by some Pi).


def implies_on_traces(p: LTL, f: LTL, traces: List[List[str]]) -> bool:
    return all((not check(p, t)) or check(f, t) for t in traces)


def _demo_soundness_completeness() -> None:
    print("--- 7.5.2 Task-failure decomposition: soundness vs. completeness ---")

    # F: the task eventually fails.
    failure = Eventually(Prop("fail"))
    # P1: persistent mis-classification. P2: deferred action for too long.
    p1 = Eventually(Prop("misclassify"))
    p2 = Eventually(Prop("deferTooLong"))

    traces = [
        ["scan", "misclassify", "fail"],       # P1 causes failure
        ["scan", "deferTooLong", "fail"],      # P2 causes failure
        ["scan", "classify", "resolve"],       # no pattern, no failure
        ["scan", "contraryDecision", "fail"],  # a *third*, uncovered cause of failure
    ]

    sound = implies_on_traces(p1, failure, traces) and implies_on_traces(p2, failure, traces)
    complete = all((not check(failure, t)) or check(p1, t) or check(p2, t) for t in traces)

    print(f"  decomposition {{P1=misclassify, P2=deferTooLong}} sound (each Pi => F)? {sound}")
    print(f"  decomposition complete (F => P1 or P2)? {complete}")
    counterexample = next(t for t in traces if check(failure, t) and not (check(p1, t) or check(p2, t)))
    print(f"  counterexample to completeness: {counterexample}")
    print("  (mirrors Example 66.3: Lindsay & Connelly's decomposition was sound but not complete --")
    print("   PAT's counterexample revealed a missing 'contrary decision process' pattern)")


if __name__ == "__main__":
    _demo_atm_closure()
    print()
    _demo_ltl_verification()
    print()
    _demo_soundness_completeness()
