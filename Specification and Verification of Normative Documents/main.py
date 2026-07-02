"""Companion code for Chapter 6, "Specification and Verification of
Normative Documents" (Roggenbach et al., *Formal Methods for Software
Engineering*).

A note on sourcing: this chapter is unusually formula-heavy (the contract
language's syntax/semantics live in Figs. 6.2-6.6, and Examples 55, 56,
56.1, 58-63 all hinge on symbolic CL formulas). Those figures and inline
formulas are typeset as images/MathML in the source and did not survive
plain-text extraction -- only the surrounding prose did. So rather than
claim a transcription of the book's exact trace-semantics rules, this file
implements an *original* formalization of the contract language grounded
in what the prose does clearly establish:

- the syntax: obligation O(a, C) with reparation C, prohibition F(a, C)
  with reparation C, permission P(a), conjunction, and the dynamic-logic
  style condition [a]C (Sec. 6.4.1);
- the deontic reading of a residual contract at each step (Sec. 6.4.2.1's
  prose walk-through of "after a is performed, an obligation to do b is
  enacted...");
- Definition 1's four conflict cases, stated in prose in Sec. 6.5.1.1.

Where the book's own worked examples (Examples 56, 58, 59) can't be
checked against this file (their formulas are the missing images), the
demo instead reproduces Example 57's fully-prose-recoverable point about
airport ground-crew contracts: an *apparent* normative conflict that is
really just an artifact of abstracting time away.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ===========================================================================
# The contract language: syntax (Sec. 6.4.1) and a residual/step semantics
# ===========================================================================

Action = FrozenSet[str]  # a set of concurrent basic actions, e.g. {"open"}


class Contract:
    pass


@dataclass(frozen=True)
class Fulfilled(Contract):
    """The trivially satisfied contract -- nothing further is required."""


@dataclass(frozen=True)
class Violated(Contract):
    """The breach sink -- the contract has already been broken."""


@dataclass(frozen=True)
class Obligation(Contract):
    """O(action, reparation): `action` is due on the very next step; if
    anything else happens instead, `reparation` (a Contrary-to-Duty
    clause) takes over."""

    action: Action
    reparation: Contract


@dataclass(frozen=True)
class Prohibition(Contract):
    """F(action, reparation): `action` must not happen; if it does,
    `reparation` (a Contrary-to-Prohibition clause) takes over. Unlike
    Obligation, a standing ban persists across steps until violated."""

    action: Action
    reparation: Contract


@dataclass(frozen=True)
class Permission(Contract):
    """P(action): a standing right. Never itself violated -- it only
    matters for conflict detection against a co-active Prohibition."""

    action: Action


@dataclass(frozen=True)
class And(Contract):
    """Conjunction of two clauses -- both must hold."""

    left: Contract
    right: Contract


@dataclass(frozen=True)
class Condition(Contract):
    """[trigger]then: `then` only becomes active once `trigger` occurs;
    until then it is a standing, dormant rule."""

    trigger: Action
    then: Contract


def _conjoin(left: Contract, right: Contract) -> Contract:
    if isinstance(left, Violated) or isinstance(right, Violated):
        return Violated()
    if isinstance(left, Fulfilled):
        return right
    if isinstance(right, Fulfilled):
        return left
    return And(left, right)


def step(contract: Contract, performed: Action) -> Contract:
    """The residual contract after `performed` happens -- what remains to
    be satisfied (cf. the residual function f, Fig. 6.4, reconstructed
    here from the chapter's prose rather than the missing figure)."""
    if isinstance(contract, (Fulfilled, Violated)):
        return contract
    if isinstance(contract, Obligation):
        return Fulfilled() if performed == contract.action else contract.reparation
    if isinstance(contract, Prohibition):
        return contract.reparation if performed == contract.action else contract
    if isinstance(contract, Permission):
        return contract
    if isinstance(contract, And):
        return _conjoin(step(contract.left, performed), step(contract.right, performed))
    if isinstance(contract, Condition):
        return contract.then if performed == contract.trigger else contract
    raise TypeError(f"unknown contract node: {contract!r}")


def run(contract: Contract, trace: List[Action]) -> Contract:
    for performed in trace:
        contract = step(contract, performed)
    return contract


def is_violated(contract: Contract) -> bool:
    return isinstance(contract, Violated)


# ===========================================================================
# Conflict analysis (Sec. 6.5.1, Definition 1)
# ===========================================================================


def active_deontics(contract: Contract) -> Set[Tuple[str, Action]]:
    """The set of (modality, action) pairs currently in force at the top
    level of a residual contract -- 'O', 'F', or 'P' paired with an
    action. Reparations (hypothetical futures) and un-triggered
    Conditions don't count as *currently* active."""
    if isinstance(contract, Obligation):
        return {("O", contract.action)}
    if isinstance(contract, Prohibition):
        return {("F", contract.action)}
    if isinstance(contract, Permission):
        return {("P", contract.action)}
    if isinstance(contract, And):
        return active_deontics(contract.left) | active_deontics(contract.right)
    return set()


def has_conflict(contract: Contract, mutually_exclusive: Set[FrozenSet[Action]]) -> bool:
    """Definition 1's four conflict cases, checked against the deontic
    information active in the current residual contract:
      (i)   the same action is both obliged and forbidden,
      (ii)  the same action is both permitted and forbidden,
      (iii) two mutually exclusive actions are both obliged,
      (iv)  one of two mutually exclusive actions is obliged, the other permitted.
    """
    active = active_deontics(contract)
    obligations = {a for m, a in active if m == "O"}
    prohibitions = {a for m, a in active if m == "F"}
    permissions = {a for m, a in active if m == "P"}

    if obligations & prohibitions:  # (i)
        return True
    if permissions & prohibitions:  # (ii)
        return True
    for pair in mutually_exclusive:
        x, y = tuple(pair)
        if x in obligations and y in obligations:  # (iii)
            return True
        if (x in obligations and y in permissions) or (y in obligations and x in permissions):  # (iv)
            return True
    return False


def find_conflict(
    contract: Contract,
    candidate_steps: List[Action],
    mutually_exclusive: Set[FrozenSet[Action]],
    max_steps: int = 4,
) -> Optional[Tuple[Action, ...]]:
    """A direct, bounded reachability search for a conflicting state
    (mirroring the *purpose* of CLAN's automaton-based algorithm, Sec.
    6.5.1.3, though not its automaton-construction machinery)."""
    frontier: deque = deque([((), contract)])
    while frontier:
        trace, cur = frontier.popleft()
        if has_conflict(cur, mutually_exclusive):
            return trace
        if len(trace) >= max_steps or is_violated(cur):
            continue
        for act in candidate_steps:
            frontier.append((trace + (act,), step(cur, act)))
    return None


def act(*names: str) -> Action:
    return frozenset(names)


def mutex(*pairs: Tuple[Action, Action]) -> Set[FrozenSet[Action]]:
    return {frozenset(p) for p in pairs}


# ===========================================================================
# Demo 1: Definition 1's four conflict cases, as minimal contracts
# ===========================================================================


def _demo_four_conflict_cases() -> None:
    print("--- 6.5.1.1 Definition 1: the four kinds of normative conflict ---")

    a, b = act("a"), act("b")

    obliged_and_forbidden = And(Obligation(a, Violated()), Prohibition(a, Violated()))
    print(f"  (i)   O(a) & F(a):        conflict? {has_conflict(obliged_and_forbidden, set())}")

    permitted_and_forbidden = And(Permission(a), Prohibition(a, Violated()))
    print(f"  (ii)  P(a) & F(a):        conflict? {has_conflict(permitted_and_forbidden, set())}")

    obliged_both_exclusive = And(Obligation(a, Violated()), Obligation(b, Violated()))
    excl = mutex((a, b))
    print(f"  (iii) O(a) & O(b), a#b:   conflict? {has_conflict(obliged_both_exclusive, excl)}")

    obliged_and_permitted_exclusive = And(Obligation(a, Violated()), Permission(b))
    print(f"  (iv)  O(a) & P(b), a#b:   conflict? {has_conflict(obliged_and_permitted_exclusive, excl)}")

    obliged_not_exclusive = And(Obligation(a, Violated()), Obligation(b, Violated()))
    print(f"  O(a) & O(b) without a#b: conflict? {has_conflict(obliged_not_exclusive, set())}"
          f"  (no declared mutual exclusion, so no conflict)")


# ===========================================================================
# Demo 2: Example 57 -- ground crew, and the abstraction pitfall
# ===========================================================================


def _demo_ground_crew() -> None:
    print("--- 6.2.2 / 6.5.1.1 Example 53 & 57: ground crew, abstraction pitfalls ---")

    open_desk, close_desk = act("open_desk"), act("close_desk")
    request_manifest = act("request_manifest")
    excl = mutex((open_desk, close_desk))  # cf. the book's own example of a#b

    # Clause 1: "obliged to open the desk ... two hours before the flight"
    # Clause 7: "obliged to close the desk 20 min before the flight"
    # Modelled naively -- both as unconditional, simultaneously active
    # obligations, exactly as Example 57 warns against: a machine with no
    # notion of "two hours before" vs "20 minutes before" sees only that
    # open_desk and close_desk are mutually exclusive, both obliged.
    naive = And(Obligation(open_desk, Violated()), Obligation(close_desk, Violated()))
    conflict = find_conflict(naive, [open_desk, close_desk, request_manifest], excl)
    print(f"  naive model (no temporal ordering): conflict trace = {conflict}")
    print("  -> a *spurious* conflict: any human reading the original clauses knows")
    print("     'open two hours before' happens well before 'close 20 min before'.")

    # Fixed: close only becomes obliged *after* open has happened, using
    # the dynamic-logic-style Condition to encode the missing ordering
    # (Example 57's own suggested remedy, in prose).
    fixed = And(
        Obligation(open_desk, Violated()),
        Condition(open_desk, Obligation(close_desk, Violated())),
    )
    conflict = find_conflict(fixed, [open_desk, close_desk, request_manifest], excl)
    print(f"  fixed model (close is conditioned on open having happened): conflict trace = {conflict}")

    after_open = step(fixed, open_desk)
    print(f"  after 'open_desk': active deontics = {active_deontics(after_open)}"
          f"  (close is now obliged; open's own obligation is discharged)")


if __name__ == "__main__":
    _demo_four_conflict_cases()
    print()
    _demo_ground_crew()
