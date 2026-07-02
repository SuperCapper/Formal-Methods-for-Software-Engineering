"""Companion code for Chapter 5, "Specification-Based Testing"
(Roggenbach et al., *Formal Methods for Software Engineering*).

Four small toolkits, one per major technique the chapter covers:

1. State-based test generation from a UML-style state machine (Sec. 5.2):
   the VCR power-switch example, with Algorithm 8-style coverage-directed
   test generation.
2. An LTL runtime monitor / test oracle (Sec. 5.2.3, Algorithm 7).
3. Conformance testing via Input-Output Transition Systems and the ioco
   relation (Sec. 5.3).
4. Ground-instance testing from an algebraic specification, with
   regularity/uniformity hypotheses to shrink the test suite (Sec. 5.4).

As with the other chapters' companion code, this is a teaching tool: test
generation and conformance checks are bounded/finite where the underlying
theory allows infinite behaviour (cycles, unbounded domains).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ===========================================================================
# 1. State-based testing: the VCR power switch (Sec. 5.2.1-5.2.2)
# ===========================================================================
#
# Fig. 5.3's hierarchy (three modes rec/mem/play nested inside state "on",
# with a single up-transition shared by all of them, inherited from "on")
# is flattened here into four states, but the shared up-transition keeps a
# single `goal_id` so that exercising it from *any* of rec/mem/play counts
# as covering it once -- exactly mirroring UML's composite-state semantics
# and the chapter's own claim that a 5-transition, single-test-case suite
# already achieves all-transitions coverage.


@dataclass(frozen=True)
class Transition:
    source: str
    event: str  # e.g. "dn?"
    output: str  # e.g. "100!"
    target: str
    goal_id: str  # transitions that are "the same" UML transition share this


VCR_TRANSITIONS: List[Transition] = [
    Transition("off", "dn?", "100!", "rec", "off_rec"),
    Transition("rec", "dn?", "010!", "mem", "rec_mem"),
    Transition("mem", "dn?", "001!", "play", "mem_play"),
    Transition("play", "dn?", "100!", "rec", "play_rec"),
    Transition("rec", "up?", "000!", "off", "on_off"),
    Transition("mem", "up?", "000!", "off", "on_off"),
    Transition("play", "up?", "000!", "off", "on_off"),
]
VCR_INITIAL = "off"
VCR_STATES = ["off", "rec", "mem", "play"]


def shortest_paths(transitions: List[Transition], initial: str):
    """Algorithm 8's first phase: BFS giving, for each reachable state, its
    distance from `initial` and the transition used to reach it."""
    graph: Dict[str, List[Transition]] = {}
    for t in transitions:
        graph.setdefault(t.source, []).append(t)
    length = {initial: 0}
    trans_used: Dict[str, Transition] = {}
    queue = deque([initial])
    while queue:
        s = queue.popleft()
        for t in graph.get(s, []):
            if t.target not in length:
                length[t.target] = length[s] + 1
                trans_used[t.target] = t
                queue.append(t.target)
    return length, trans_used


def path_to(state: str, trans_used: Dict[str, Transition]) -> List[Transition]:
    path = []
    cur = state
    while cur in trans_used:
        t = trans_used[cur]
        path.append(t)
        cur = t.source
    path.reverse()
    return path


def all_states_suite(transitions: List[Transition], initial: str, states: List[str]) -> List[List[Transition]]:
    """Algorithm 8: cover the most-distant uncovered state first."""
    length, trans_used = shortest_paths(transitions, initial)
    targets = sorted((s for s in states if s in length), key=lambda s: -length[s])
    covered: Set[str] = set()
    suite: List[List[Transition]] = []
    for s in targets:
        path = path_to(s, trans_used)
        states_on_path = {t.target for t in path}
        if states_on_path <= covered:
            continue
        covered |= states_on_path
        suite.append(path)
    return suite


def render(path: List[Transition]) -> Tuple[str, ...]:
    out = []
    for t in path:
        out.append(t.event)
        out.append(t.output)
    return tuple(out)


def covered_goal_ids(suite: List[List[Transition]]) -> Set[str]:
    return {t.goal_id for path in suite for t in path}


def _demo_state_based_testing() -> None:
    print("--- 5.2 VCR switch: coverage-directed test generation ---")

    suite = all_states_suite(VCR_TRANSITIONS, VCR_INITIAL, VCR_STATES)
    print(f"  all-states suite (Algorithm 8): {[render(p) for p in suite]}")
    expected = (("dn?", "100!", "dn?", "010!", "dn?", "001!"),)
    print(f"  matches the book's own suite exactly? {tuple(render(p) for p in suite) == expected}")

    all_goal_ids = {t.goal_id for t in VCR_TRANSITIONS}

    book_all_transitions_case = [
        VCR_TRANSITIONS[0], VCR_TRANSITIONS[1], VCR_TRANSITIONS[2],
        VCR_TRANSITIONS[3], VCR_TRANSITIONS[4],
    ]  # (dn?,100!, dn?,010!, dn?,001!, dn?,100!, up?,000!)
    print(f"  book's single all-transitions test case: {render(book_all_transitions_case)}")
    print(f"  covers all 5 transitions? {covered_goal_ids([book_all_transitions_case]) == all_goal_ids}")

    book_decision_coverage_suite = [
        [VCR_TRANSITIONS[0], VCR_TRANSITIONS[4]],
        [VCR_TRANSITIONS[0], VCR_TRANSITIONS[1], VCR_TRANSITIONS[5]],
        [VCR_TRANSITIONS[0], VCR_TRANSITIONS[1], VCR_TRANSITIONS[2], VCR_TRANSITIONS[6]],
        [VCR_TRANSITIONS[0], VCR_TRANSITIONS[1], VCR_TRANSITIONS[2], VCR_TRANSITIONS[3]],
    ]
    print(f"  book's decision-coverage suite covers all 5 transitions? "
          f"{covered_goal_ids(book_decision_coverage_suite) == all_goal_ids}")


# ===========================================================================
# 2. An LTL runtime monitor / test oracle (Sec. 5.2.3, Algorithm 7)
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
class And(LTL):
    left: LTL
    right: LTL


@dataclass(frozen=True)
class Or(LTL):
    left: LTL
    right: LTL


@dataclass(frozen=True)
class Implies(LTL):
    left: LTL
    right: LTL


@dataclass(frozen=True)
class Next(LTL):
    inner: LTL


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


@dataclass(frozen=True)
class WeakUntil(LTL):
    """phi W psi ("unless"): phi U psi, or phi holds forever if psi never
    comes -- used because a test trace need not end in the off-state."""

    left: LTL
    right: LTL


Trace = Tuple[str, ...]  # a sequence of ENV2SUT/SUT2ENV labels, e.g. "dn?", "100!"


def eval_ltl(f: LTL, trace: Trace, i: int) -> bool:
    """Algorithm 7's recursive unwinding (G phi = phi & X(G phi), etc.),
    with the finite-trace convention that `Next` is false once the trace
    has ended."""
    if isinstance(f, Prop):
        return i < len(trace) and trace[i] == f.name
    if isinstance(f, Not):
        return not eval_ltl(f.inner, trace, i)
    if isinstance(f, And):
        return eval_ltl(f.left, trace, i) and eval_ltl(f.right, trace, i)
    if isinstance(f, Or):
        return eval_ltl(f.left, trace, i) or eval_ltl(f.right, trace, i)
    if isinstance(f, Implies):
        return (not eval_ltl(f.left, trace, i)) or eval_ltl(f.right, trace, i)
    if isinstance(f, Next):
        return i + 1 < len(trace) and eval_ltl(f.inner, trace, i + 1)
    if isinstance(f, Always):
        return all(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    if isinstance(f, Eventually):
        return any(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    if isinstance(f, Until):
        for j in range(i, len(trace)):
            if eval_ltl(f.right, trace, j):
                return all(eval_ltl(f.left, trace, k) for k in range(i, j))
        return False
    if isinstance(f, WeakUntil):
        return eval_ltl(Until(f.left, f.right), trace, i) or eval_ltl(Always(f.left), trace, i)
    raise TypeError(f"unknown LTL node: {f!r}")


def test_oracle(f: LTL, trace: Trace) -> bool:
    """The test verdict for a trace: pass iff the oracle formula holds."""
    return eval_ltl(f, trace, 0)


def _simulate(inputs: List[str]) -> Trace:
    """Run a sequence of ?dn/?up inputs through the VCR state machine
    (Sec. 5.2.1) and record the interleaved input/output trace."""
    by_source: Dict[str, List[Transition]] = {}
    for t in VCR_TRANSITIONS:
        by_source.setdefault(t.source, []).append(t)
    state = VCR_INITIAL
    trace: List[str] = []
    for event in inputs:
        match = next((t for t in by_source.get(state, []) if t.event == event), None)
        if match is None:
            continue  # "unexpected events are skipped" (Sec. 5.2.1)
        trace.extend([match.event, match.output])
        state = match.target
    return tuple(trace)


def _demo_ltl_monitor() -> None:
    print("--- 5.2.3 LTL runtime monitor (Algorithm 7) ---")

    up_implies_off = Always(Implies(Prop("up?"), Next(Prop("000!"))))

    # "a lamp is lit until up? is pressed again" -- the trace alternates
    # input and output labels, so at each non-up? position we accept
    # either a lit lamp (an output position) or a dn? (an input position);
    # only up? itself is allowed to end the streak.
    lamp = Or(Or(Prop("100!"), Prop("010!")), Prop("001!"))
    step_ok = Or(lamp, Prop("dn?"))
    lamp_lit_until_up = Always(Implies(Prop("dn?"), Next(WeakUntil(step_ok, Prop("up?")))))

    good_trace = _simulate(["dn?", "dn?", "up?"])
    print(f"  trace for dn,dn,up: {good_trace}")
    print(f"  'up? implies next is 000!' passes?         {test_oracle(up_implies_off, good_trace)}")
    print(f"  'a lamp stays lit until up?' passes?        {test_oracle(lamp_lit_until_up, good_trace)}")

    bad_trace = ("dn?", "100!", "up?", "999!")  # a fabricated, non-conformant trace
    print(f"  fabricated violating trace: {bad_trace}")
    print(f"  'up? implies next is 000!' passes?         {test_oracle(up_implies_off, bad_trace)}")

    always_ends_off = Always(Implies(Prop("up?"), Next(Prop("000!"))))
    trace_without_up = _simulate(["dn?"])
    print(f"  trace that never presses up: {trace_without_up}")
    print(
        f"  '(lamp lit) W up?' still passes on a trace with no up? "
        f"(the 'unless' the book uses instead of 'until')? "
        f"{test_oracle(lamp_lit_until_up, trace_without_up)}"
    )


# ===========================================================================
# 3. Conformance testing with ioco (Sec. 5.3, Example 49.4)
# ===========================================================================

DELTA = "delta"  # quiescence marker


@dataclass
class IOTS:
    initial: str
    transitions: Dict[str, List[Tuple[str, str]]]  # state -> [(label, target)]


def out(iots: IOTS, state: str) -> FrozenSet[str]:
    outputs = frozenset(label for label, _ in iots.transitions.get(state, []) if label.startswith("!"))
    return outputs if outputs else frozenset({DELTA})


def after(iots: IOTS, trace: Trace) -> Optional[str]:
    """Deterministic-only: the state reached by `trace`, or None if it
    can't be performed (including a quiescence step only when quiescent)."""
    cur = iots.initial
    for label in trace:
        if label == DELTA:
            if out(iots, cur) != frozenset({DELTA}):
                return None
            continue
        match = next((t for l, t in iots.transitions.get(cur, []) if l == label), None)
        if match is None:
            return None
        cur = match
    return cur


def suspension_traces(iots: IOTS, max_len: int = 6) -> Set[Trace]:
    """Bounded traces of the suspension transition system: real
    transitions, plus a delta self-loop wherever the state is quiescent."""
    results: Set[Trace] = set()
    frontier: List[Tuple[Trace, str]] = [((), iots.initial)]
    while frontier:
        trace, state = frontier.pop()
        if trace in results:
            continue
        results.add(trace)
        if len(trace) >= max_len:
            continue
        for label, target in iots.transitions.get(state, []):
            frontier.append((trace + (label,), target))
        if out(iots, state) == frozenset({DELTA}):
            frontier.append((trace + (DELTA,), state))
    return results


def traces(iots: IOTS, max_len: int = 6) -> Set[Trace]:
    """Ordinary (non-suspension) traces, for the trace preorder."""
    results: Set[Trace] = set()
    frontier: List[Tuple[Trace, str]] = [((), iots.initial)]
    while frontier:
        trace, state = frontier.pop()
        if trace in results:
            continue
        results.add(trace)
        if len(trace) >= max_len:
            continue
        for label, target in iots.transitions.get(state, []):
            frontier.append((trace + (label,), target))
    return results


def trace_preorder(impl: IOTS, spec: IOTS, max_len: int = 6) -> bool:
    return traces(impl, max_len) <= traces(spec, max_len)


def ioco(impl: IOTS, spec: IOTS, max_len: int = 6) -> Tuple[bool, Optional[Trace]]:
    for sigma in suspension_traces(spec, max_len):
        impl_state = after(impl, sigma)
        if impl_state is None:
            continue  # impl can't perform sigma -- vacuously fine
        spec_state = after(spec, sigma)
        if not out(impl, impl_state) <= out(spec, spec_state):
            return False, sigma
    return True, None


SP_ABSTRACT = IOTS(
    initial="off",
    transitions={
        "off": [("?dn", "t1")],
        "t1": [("!100", "on")],
        "on": [("?up", "t2")],
        "t2": [("!000", "off")],
    },
)

SP_ABSTRACT_WITH_BATTERY_FAILURE = IOTS(
    initial="off",
    transitions={
        "off": [("?dn", "t1")],
        "t1": [("!100", "on")],
        "on": [("?up", "t2"), ("!shutdown", "off")],  # spontaneous battery failure
        "t2": [("!000", "off")],
    },
)

SP_REFINED = IOTS(
    initial="off",
    transitions={
        "off": [("?dn", "i1")],
        "i1": [("!100", "rec")],
        "rec": [("?dn", "i2"), ("?up", "i5")],
        "i2": [("!010", "mem")],
        "mem": [("?dn", "i3"), ("?up", "i6")],
        "i3": [("!001", "play")],
        "play": [("?dn", "i4"), ("?up", "i7")],
        "i4": [("!100", "rec")],
        "i5": [("!000", "off")],
        "i6": [("!000", "off")],
        "i7": [("!000", "off")],
    },
)


def _demo_ioco() -> None:
    print("--- 5.3 Conformance testing: ioco (Example 49.4) ---")

    ok = trace_preorder(SP_REFINED, SP_ABSTRACT)
    print(f"  sp_refined traces subset-of sp_abstract traces? {ok}  (refined does *more*, so this is False)")

    ok, witness = ioco(SP_REFINED, SP_ABSTRACT)
    print(f"  sp_refined ioco sp_abstract? {ok}")
    print("  (ioco only constrains behaviour at traces sp_abstract itself can perform --")
    print("   refined's extra dn-presses fall outside that, so they don't break conformance)")

    ok = trace_preorder(SP_REFINED, SP_ABSTRACT_WITH_BATTERY_FAILURE)
    print(f"  with a spontaneous battery-failure output added to the spec:")
    print(f"    sp_refined traces subset-of modified sp_abstract traces? {ok}  (still True -- more spec behaviour, not less)")
    ok, witness = ioco(SP_REFINED, SP_ABSTRACT_WITH_BATTERY_FAILURE)
    print(f"    sp_refined ioco modified sp_abstract? {ok}  (witness: {witness})")
    print("    (refined is quiescent in 'on' where the spec insists it must be able to shut down --")
    print("     trace-preorder can't see this, ioco can)")


# ===========================================================================
# 4. Ground-instance testing from an algebraic spec (Sec. 5.4, Example 50)
# ===========================================================================


def is_leap_year(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def dim(month: int, year: int) -> int:
    """The reference implementation of Example 50's DaysInMonth spec."""
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if month == 2:
        return 29 if is_leap_year(year) else 28
    raise ValueError(f"month {month} out of range")


def _buggy_is_leap_year(y: int) -> bool:
    """A plausible bug: forgets the %400 exception, so century years like
    2000 are (wrongly) never treated as leap years."""
    return y % 4 == 0 and y % 100 != 0


def buggy_dim(month: int, year: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if month == 2:
        return 29 if _buggy_is_leap_year(year) else 28
    raise ValueError(f"month {month} out of range")


def run_ground_suite(suite: List[Tuple[int, int]], impl) -> Optional[Tuple[int, int]]:
    """A test case here is a ground instance (m, y) of the universally
    quantified specification formula 'dim(m, y) = <reference value>'."""
    for m, y in suite:
        if impl(m, y) != dim(m, y):
            return (m, y)
    return None


def _demo_algebraic_testing() -> None:
    print("--- 5.4 Algebraic specification testing: the dim-function (Example 50) ---")

    full_suite = [(m, y) for m in range(1, 13) for y in range(1583, 1583 + 500)]
    print(f"  'full' ground-instance suite (Example 50): {len(full_suite)} test cases")
    counterexample = run_ground_suite(full_suite, buggy_dim)
    print(f"  buggy dim (forgets the /400 exception) fails at: dim{counterexample}")

    # Example 50.2: uniformity hypothesis -- isLeapYear behaves uniformly
    # within each of these four classes, so one representative per class
    # suffices, *provided* the hypothesis is actually justified for the SUT.
    uniformity_classes = {
        "div_by_400": [2000, 2400],
        "div_by_100_not_400": [1900, 2100],
        "div_by_4_not_100": [1996, 2004],
        "not_div_by_4": [1997, 2001],
    }
    representatives = [years[0] for years in uniformity_classes.values()]
    reduced_suite = [(m, y) for m in range(1, 13) for y in representatives]
    print(f"  uniformity-hypothesis-reduced suite: {len(reduced_suite)} test cases"
          f" ({len(full_suite) // len(reduced_suite)}x smaller)")
    counterexample = run_ground_suite(reduced_suite, buggy_dim)
    print(f"  still catches the bug at: dim{counterexample}")

    # A correct implementation should pass both suites cleanly.
    print(f"  reference implementation passes the full suite? {run_ground_suite(full_suite, dim) is None}")


if __name__ == "__main__":
    _demo_state_based_testing()
    print()
    _demo_ltl_monitor()
    print()
    _demo_ioco()
    print()
    _demo_algebraic_testing()
