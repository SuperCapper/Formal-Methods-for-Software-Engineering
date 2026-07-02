"""Companion code for Chapter 3, "The Process Algebra CSP"
(Roggenbach et al., *Formal Methods for Software Engineering*, pgs. 164-261).

A small, bounded-depth CSP engine mirroring the chapter's operational
semantics (Sec. 3.2.2, firing rules) and traces model (Sec. 3.4.1), plus a
plain-Python simulation of the Children's Puzzle (Sec. 3.3.1).

This is a *teaching* tool, not a model checker like FDR: trace generation,
deadlock-freedom, and refinement checks are all bounded to a small number
of visible events (`max_events`), and processes are explored by following
every branch rather than by hashing/merging equivalent states. That is
enough to reproduce the chapter's own (small, finite) examples and to
build genuine intuition for traces, deadlock, and refinement -- but it is
not a decision procedure for arbitrary CSP processes.

Not implemented (left as natural extensions): the interrupt operator
(Sec. 3.2.1), replicated process operators, and the failures/divergences
and stable-failures models (Sec. 3.4.1) -- only enough of the traces model
plus a simple deadlock check (Sec. 3.4.4) is built here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Iterator, List, Optional, Tuple

TAU = object()  # the silent/internal event tau, cf. Sec. 3.2.2
TICK = "tick"  # Csp's termination event, written surd in the book


# ===========================================================================
# 1. Process syntax (Sec. 3.2.1) and operational semantics (Sec. 3.2.2)
# ===========================================================================


class Process:
    """Base class; concrete processes are the dataclasses below."""


@dataclass
class Stop(Process):
    """STOP: refuses every event, forever."""


@dataclass
class Skip(Process):
    """SKIP: immediately performs tick and terminates."""


@dataclass
class Prefix(Process):
    """a -> P: perform event a, then behave as P."""

    event: str
    cont: Process


@dataclass
class PrefixChoice(Process):
    """c?x -> P(x): let the environment pick any event from `events`."""

    events: FrozenSet[str]
    cont: Callable[[str], Process]


@dataclass
class ExtChoice(Process):
    """P [] Q: environment's first visible event resolves the choice."""

    left: Process
    right: Process


@dataclass
class IntChoice(Process):
    """P |~| Q: the process itself silently resolves the choice."""

    left: Process
    right: Process


@dataclass
class Seq(Process):
    """P ; Q: behave as P; once P performs tick, silently continue as Q."""

    left: Process
    right: Process


@dataclass
class GenParallel(Process):
    """P [|A|] Q: P and Q run together, synchronising on events in `sync`."""

    left: Process
    right: Process
    sync: FrozenSet[str]


@dataclass
class Hide(Process):
    """P \\ A: events in `hidden` become invisible (turned into tau)."""

    inner: Process
    hidden: FrozenSet[str]


@dataclass
class Rename(Process):
    """P[[R]]: rename visible events through the mapping R."""

    inner: Process
    mapping: Dict[str, str]


@dataclass
class Rec(Process):
    """A recursive process, given as a thunk so Python can build the
    (conceptually infinite) unfolding lazily, e.g. ``Rec(lambda: ATM())``.
    """

    thunk: Callable[[], Process]


def transitions(p: Process) -> Iterator[Tuple[object, Process]]:
    """The firing rules of Sec. 3.2.2 / Appendix B.3: yields (event, P') pairs.

    `event` is either the sentinel TAU, the string TICK, or a visible event
    name.
    """
    if isinstance(p, Stop):
        return
    if isinstance(p, Skip):
        yield (TICK, Stop())
        return
    if isinstance(p, Prefix):
        yield (p.event, p.cont)
        return
    if isinstance(p, PrefixChoice):
        for e in p.events:
            yield (e, p.cont(e))
        return
    if isinstance(p, ExtChoice):
        for e, l2 in transitions(p.left):
            if e is TAU:
                yield (TAU, ExtChoice(l2, p.right))
            else:
                yield (e, l2)
        for e, r2 in transitions(p.right):
            if e is TAU:
                yield (TAU, ExtChoice(p.left, r2))
            else:
                yield (e, r2)
        return
    if isinstance(p, IntChoice):
        yield (TAU, p.left)
        yield (TAU, p.right)
        return
    if isinstance(p, Seq):
        for e, l2 in transitions(p.left):
            if e == TICK:
                yield (TAU, p.right)
            else:
                yield (e, Seq(l2, p.right))
        return
    if isinstance(p, GenParallel):
        for e, l2 in transitions(p.left):
            if e is TAU:
                yield (TAU, GenParallel(l2, p.right, p.sync))
            elif e not in p.sync:
                yield (e, GenParallel(l2, p.right, p.sync))
        for e, r2 in transitions(p.right):
            if e is TAU:
                yield (TAU, GenParallel(p.left, r2, p.sync))
            elif e not in p.sync:
                yield (e, GenParallel(p.left, r2, p.sync))
        for e, l2 in transitions(p.left):
            if e is TAU or e not in p.sync:
                continue
            for e2, r2 in transitions(p.right):
                if e2 == e:
                    yield (e, GenParallel(l2, r2, p.sync))
        return
    if isinstance(p, Hide):
        for e, i2 in transitions(p.inner):
            if e is TAU:
                yield (TAU, Hide(i2, p.hidden))
            elif e in p.hidden:
                yield (TAU, Hide(i2, p.hidden))
            else:
                yield (e, Hide(i2, p.hidden))
        return
    if isinstance(p, Rename):
        for e, i2 in transitions(p.inner):
            if e is TAU:
                yield (TAU, Rename(i2, p.mapping))
            else:
                yield (p.mapping.get(e, e), Rename(i2, p.mapping))
        return
    if isinstance(p, Rec):
        yield (TAU, p.thunk())
        return
    raise TypeError(f"unknown process node: {p!r}")


# ===========================================================================
# 2. The traces model (Sec. 3.4.1) and deadlock-freedom (Sec. 3.4.4, Def. 7)
# ===========================================================================


def stable_states(p: Process, tau_budget: int = 500) -> List[Process]:
    """Tau-closure of p: the stable configurations reachable via tau steps.

    Several stable states can arise from one process (e.g. via internal
    choice) -- this mirrors the ButtonOFF discussion around Fig. 3.2/3.3.
    """
    result: List[Process] = []
    frontier: List[Process] = [p]
    budget = tau_budget
    while frontier:
        cur = frontier.pop()
        taus = [nxt for (e, nxt) in transitions(cur) if e is TAU]
        if not taus:
            result.append(cur)
            continue
        budget -= len(taus)
        if budget < 0:
            raise RuntimeError(
                "tau-closure exceeded its budget -- the process may diverge/livelock"
            )
        frontier.extend(taus)
    return result


def traces(p: Process, max_events: int = 6, max_nodes: int = 20000) -> set:
    """All (prefix-closed) observable traces reachable within max_events
    visible events -- a bounded approximation of the traces domain T
    (Sec. 3.4.1)."""
    results = set()
    frontier: List[Tuple[tuple, Process]] = [((), s) for s in stable_states(p)]
    count = 0
    while frontier:
        trace, state = frontier.pop()
        if trace in results:
            continue
        results.add(trace)
        count += 1
        if count > max_nodes or len(trace) >= max_events:
            continue
        for e, nxt in transitions(state):
            if e is TAU:
                continue
            for s2 in stable_states(nxt):
                frontier.append((trace + (e,), s2))
    return results


def deadlock_free(
    p: Process, max_events: int = 6, max_nodes: int = 20000
) -> Tuple[bool, Optional[tuple]]:
    """Bounded check for Definition 7 (deadlock-freedom): explores every
    branch up to max_events visible events, looking for a stable state
    that offers no events at all. Returns (True, None) if none is found
    within the bound, else (False, witness_trace)."""
    frontier: List[Tuple[tuple, Process]] = [((), s) for s in stable_states(p)]
    seen = 0
    while frontier:
        trace, state = frontier.pop()
        seen += 1
        if seen > max_nodes:
            return True, None
        outgoing = list(transitions(state))
        if not outgoing:
            return False, trace
        if len(trace) >= max_events:
            continue
        for e, nxt in outgoing:
            for s2 in stable_states(nxt):
                frontier.append((trace + (e,), s2))
    return True, None


def trace_refines(spec: Process, impl: Process, max_events: int = 6) -> bool:
    """impl [T= spec, bounded to max_events (Sec. 3.2.3 / 3.4.1): every
    (bounded) trace of impl must also be a trace of spec."""
    return traces(impl, max_events) <= traces(spec, max_events)


# ===========================================================================
# Demo 1 (Sec. 3.2.1): the ATM, ATM1 -- ordering events via recursion
# ===========================================================================


def _demo_atm() -> None:
    print("--- 3.2.1 ATM: recursion and a total event order ---")

    def atm() -> Process:
        return Prefix(
            "cardI",
            Prefix("pinE", Prefix("cashO", Prefix("cardO", Rec(atm)))),
        )

    atm_traces = sorted(traces(Rec(atm), max_events=6))
    for t in atm_traces[:6]:
        print(f"  {t}")
    print(f"  ({len(atm_traces)} traces up to 6 events -- a single strict order)")

    # Sec. "Internal Choice, System Composition, Abstraction by Hiding":
    # hiding cardI makes it invisible without changing the remaining order.
    hidden = Hide(Rec(atm), frozenset({"cardI"}))
    print(f"  after hiding cardI, one trace is: {sorted(traces(hidden, 4))[-1]}")


# ===========================================================================
# Demo 2 (Sec. 3.1): the bistro story -- protocol mismatch causes deadlock
# ===========================================================================


def _demo_bistro_deadlock() -> None:
    print("--- 3.1 Bistro story: mismatched protocols deadlock ---")

    customer = Prefix("item", Prefix("pay", Stop()))
    waiter_mismatched = Prefix("pay", Prefix("item", Stop()))
    waiter_matched = Prefix("item", Prefix("pay", Stop()))

    mismatched = GenParallel(customer, waiter_mismatched, frozenset({"item", "pay"}))
    matched = GenParallel(customer, waiter_matched, frozenset({"item", "pay"}))

    ok, witness = deadlock_free(mismatched)
    print(f"  customer wants item-then-pay, waiter wants pay-then-item")
    print(f"  deadlock_free? {ok}  (witness trace: {witness})")
    print(f"  traces: {sorted(traces(mismatched, 4))}")

    ok, witness = deadlock_free(matched)
    print(f"  both want item-then-pay")
    print(f"  deadlock_free? {ok}  (witness trace: {witness})")
    print(f"  traces: {sorted(traces(matched, 4))}")
    print(
        "  (note: this simplified checker treats STOP after full completion the"
        " same as a real deadlock -- see 3.2.1's SKIP/tick discussion. The"
        " mismatched case deadlocks at the *empty* trace (), a real protocol"
        " bug; the matched case only 'stops' at the witness trace above, i.e."
        " only after the whole protocol has already completed successfully)"
    )


# ===========================================================================
# Demo 3 (Sec. 3.2.3): BUFF -- the characteristic buffer, and refinement
# ===========================================================================

MESSAGES = ("a", "b")


def buff(q: Tuple[str, ...] = ()) -> Process:
    """The buffer of Example 38.4: empty buffers always accept input;
    non-empty buffers may (internal choice) refuse further input, but
    always offer to write out their head."""

    def thunk() -> Process:
        read_events = frozenset(f"read.{m}" for m in MESSAGES)

        def read_cont(e: str) -> Process:
            m = e.split(".", 1)[1]
            return Rec(lambda: buff(q + (m,)))

        read_choice = PrefixChoice(read_events, read_cont)
        if not q:
            return read_choice
        write_branch = Prefix(f"write.{q[0]}", Rec(lambda: buff(q[1:])))
        maybe_read = IntChoice(read_choice, Stop())
        return ExtChoice(maybe_read, write_branch)

    return Rec(thunk)


def two_place_buffer(q: Tuple[str, ...] = ()) -> Process:
    """A concrete two-place buffer, cf. Example 38.7: reads whenever there
    is room, writes whenever non-empty -- no internal refusal of input."""

    def thunk() -> Process:
        read_events = frozenset(f"read.{m}" for m in MESSAGES)

        def read_cont(e: str) -> Process:
            m = e.split(".", 1)[1]
            return Rec(lambda: two_place_buffer(q + (m,)))

        branches = []
        if len(q) < 2:
            branches.append(PrefixChoice(read_events, read_cont))
        if q:
            branches.append(Prefix(f"write.{q[0]}", Rec(lambda: two_place_buffer(q[1:]))))
        if len(branches) == 2:
            return ExtChoice(branches[0], branches[1])
        return branches[0]

    return Rec(thunk)


def _split_trace(trace: tuple) -> Tuple[list, list]:
    reads = [e.split(".", 1)[1] for e in trace if e.startswith("read.")]
    writes = [e.split(".", 1)[1] for e in trace if e.startswith("write.")]
    return reads, writes


def _demo_buffer() -> None:
    print("--- 3.2.3 BUFF: the prefix property, deadlock-freedom, refinement ---")

    all_traces = traces(buff(), max_events=8)
    violations = 0
    for t in all_traces:
        reads, writes = _split_trace(t)
        if writes != reads[: len(writes)]:
            violations += 1
    print(
        f"  checked property (3.1) 'writes are a prefix of reads' on"
        f" {len(all_traces)} traces: {violations} violations"
    )

    ok, witness = deadlock_free(buff(), max_events=6)
    print(f"  BUFF is deadlock-free (bounded check)? {ok}")

    refines = trace_refines(buff(), two_place_buffer(), max_events=6)
    print(f"  two_place_buffer [T= BUFF (Example 38.7-style refinement)? {refines}")


# ===========================================================================
# Demo 4 (Sec. 3.2.1): SKIP and sequential composition, sanity check
# ===========================================================================


def _demo_seq_skip() -> None:
    print("--- 3.2.1 SKIP and sequential composition ---")
    p = Seq(Prefix("a", Skip()), Prefix("b", Stop()))
    print(f"  traces of (a -> SKIP) ; (b -> STOP): {sorted(traces(p, 4))}")


# ===========================================================================
# Demo 5 (Sec. 3.3.1): the Children's Puzzle, arithmetic simulation
# ===========================================================================


def puzzle_round(candies: List[int], neighbour_left: List[int]) -> List[int]:
    """One synchronous round (Step 1 + Step 2) of Example 40."""
    given = [c // 2 for c in candies]
    after_step1 = [c - g for c, g in zip(candies, given)]
    for i, g in enumerate(given):
        after_step1[neighbour_left[i]] += g
    return [c + (1 if c % 2 else 0) for c in after_step1]


def run_puzzle(
    candies: List[int], neighbour_left: List[int], max_rounds: int = 200
) -> List[Tuple[int, ...]]:
    history = [tuple(candies)]
    for _ in range(max_rounds):
        if len(set(candies)) == 1:
            break
        candies = puzzle_round(candies, neighbour_left)
        history.append(tuple(candies))
    return history


def _demo_childrens_puzzle() -> None:
    print("--- 3.3.1 Children's Puzzle: arithmetic simulation ---")

    # Example 40.1: Berta=0, Emma=2, Hugo=4; each child's left neighbour
    # receives from them (Berta->Emma->Hugo->Berta).
    names = ["Berta", "Emma", "Hugo"]
    neighbour_left = [1, 2, 0]
    history = run_puzzle([0, 2, 4], neighbour_left)
    for round_no, state in enumerate(history):
        print(f"  round {round_no}: " + ", ".join(f"{n}={c}" for n, c in zip(names, state)))
    print(f"  stabilised after {len(history) - 1} round(s), matching Example 40.1/40.4")

    # Corollary 2, empirically, for random instances (must start even, Def.).
    random.seed(0)
    rounds_needed = []
    for _ in range(20):
        n = random.randint(3, 8)
        candies = [random.randint(0, 10) * 2 for _ in range(n)]
        left = [(i + 1) % n for i in range(n)]
        h = run_puzzle(candies, left)
        rounds_needed.append(len(h) - 1)
    print(
        f"  20 random instances (3-8 children) all stabilised;"
        f" rounds needed: min={min(rounds_needed)}, max={max(rounds_needed)}"
    )


if __name__ == "__main__":
    _demo_atm()
    print()
    _demo_bistro_deadlock()
    print()
    _demo_buffer()
    print()
    _demo_seq_skip()
    print()
    _demo_childrens_puzzle()
