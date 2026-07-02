"""Companion code for Chapter 4, "Algebraic Specification in CASL"
(Roggenbach et al., *Formal Methods for Software Engineering*, pgs. 262-320).

Three small toolkits, each mirroring a section of the chapter:

1. The Telephone Database (Sec. 4.2): a reference implementation of the
   specification's abstract data type, plus a ConGu-style random axiom
   checker (Sec. 4.2.4) that can catch both implementation bugs and
   specification bugs.
2. Ladder Logic / a Pelican Crossing (Sec. 4.3): a transition relation
   over boolean state, its reachable-state automaton (Def. 6-7), a direct
   check of the verification problem (Def. 8), and inductive verification
   (Sec. 4.3.4).
3. Signature structuring (Sec. 4.4): extension, union, and renaming
   implemented directly on signatures, matching Casl's "same name, same
   thing" semantics.

This is a teaching tool, not Hets/SPASS: there is no general first-order
theorem prover here. Where the chapter proves a property with SPASS, this
file instead checks it either exhaustively over a small finite state space
(the ladder logic automaton) or by extensive random testing (the database
axioms) -- sound as far as it goes, but not a proof.
"""

from __future__ import annotations

import itertools
import random
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

# ===========================================================================
# 1. The Telephone Database (Sec. 4.2)
# ===========================================================================
#
# Database is represented as a tuple of (name, number) pairs, most recently
# updated entry first -- directly mirroring the term-algebra reading of
# Example 43.1's signature (initial, update, lookUp, delete, isEmpty).

Database = Tuple[Tuple[str, str], ...]

NAMES = ("Hugo", "Erna", "Ida")  # cf. Example 43.3: "Hugo different from Erna"
NUMBERS = ("N4711", "N17", "N999")


def initial() -> Database:
    return ()


def update(db: Database, name: str, number: str) -> Database:
    return ((name, number),) + db


def lookup(db: Database, name: str) -> Optional[str]:
    for n, number in db:
        if n == name:
            return number
    return None  # "undefined", cf. %(non_def_initial)%


def delete(db: Database, name: str) -> Database:
    """Recursive delete, matching Example 43.2's %(delete_found)% /
    %(delete_not_found)% axioms: remove *every* entry for `name`, most
    recent first."""
    if not db:
        return db
    (n, number), rest = db[0], db[1:]
    if n == name:
        return delete(rest, name)
    return ((n, number),) + delete(rest, name)


def is_empty(db: Database) -> bool:
    return len(db) == 0


@dataclass
class DatabaseImpl:
    """A swappable implementation, so the axiom checker below can be
    pointed at either the reference implementation or a buggy one."""

    initial: Callable[[], Database]
    update: Callable[[Database, str, str], Database]
    lookup: Callable[[Database, str], Optional[str]]
    delete: Callable[[Database, str], Database]
    is_empty: Callable[[Database], bool]


REFERENCE = DatabaseImpl(initial, update, lookup, delete, is_empty)


def _buggy_lookup_oldest(db: Database, name: str) -> Optional[str]:
    """Example 43.13's bug: scans oldest-first, so a name updated more
    than once returns a *stale* number instead of the most recent one."""
    for n, number in reversed(db):
        if n == name:
            return number
    return None


BUGGY_IMPLEMENTATION = DatabaseImpl(initial, update, _buggy_lookup_oldest, delete, is_empty)


def _buggy_update_forgot_negation(db: Database, name: str, number: str) -> Database:
    """Example 43.14's bug: a specifier's typo -- forgetting a negation in
    the 'name not found' rung turns %(name_found)% and %(name_not_found)%
    into contradictory requirements. Modelled here by an update that
    (incorrectly) *always* overwrites in place rather than pushing a new
    most-recent entry, silently dropping the shadowed history."""
    return tuple((n, number) if n == name else (n, num) for n, num in db) or ((name, number),)


BUGGY_SPEC = DatabaseImpl(initial, _buggy_update_forgot_negation, lookup, delete, is_empty)


def random_db(impl: DatabaseImpl, rng: random.Random, max_ops: int) -> Database:
    db = impl.initial()
    for _ in range(rng.randint(0, max_ops)):
        db = impl.update(db, rng.choice(NAMES), rng.choice(NUMBERS))
    return db


def check_axioms(
    impl: DatabaseImpl, trials: int = 300, max_ops: int = 6, seed: int = 0
) -> Tuple[Optional[int], Optional[tuple]]:
    """A ConGu-style random-runner (Sec. 4.2.4): on each trial, build a
    random database and check Example 43.2's axioms against it. Returns
    (trial_number, description) for the first violation found, or
    (None, None) if none turned up within `trials` attempts."""
    rng = random.Random(seed)
    for trial in range(1, trials + 1):
        db = random_db(impl, rng, max_ops)
        name, name2 = rng.choice(NAMES), rng.choice(NAMES)
        number = rng.choice(NUMBERS)

        if impl.lookup(impl.initial(), name) is not None:
            return trial, ("non_def_initial", name)

        if impl.lookup(impl.update(db, name, number), name) != number:
            return trial, ("name_found", db, name, number)

        if name2 != name:
            expected = impl.lookup(db, name2)
            if impl.lookup(impl.update(db, name, number), name2) != expected:
                return trial, ("name_not_found", db, name, name2, number)

        if impl.delete(impl.initial(), name) != impl.initial():
            return trial, ("delete_initial", name)

        if impl.delete(impl.update(db, name, number), name) != impl.delete(db, name):
            return trial, ("delete_found", db, name, number)

        if name2 != name:
            lhs = impl.delete(impl.update(db, name, number), name2)
            rhs = impl.update(impl.delete(db, name2), name, number)
            if lhs != rhs:
                return trial, ("delete_not_found", db, name, name2, number)

        if impl.is_empty(db) != (db == impl.initial()):
            return trial, ("def_isEmpty", db)

    return None, None


def check_specialised_commutativity(trials: int = 300, seed: int = 1) -> bool:
    """Example 43.4: swapping two updates for *different* names doesn't
    change what lookUp observes -- should hold."""
    rng = random.Random(seed)
    for _ in range(trials):
        db = random_db(REFERENCE, rng, 5)
        n1, n2 = rng.sample(NAMES, 2)
        x1, x2 = rng.choice(NUMBERS), rng.choice(NUMBERS)
        ab = update(update(db, n1, x1), n2, x2)
        ba = update(update(db, n2, x2), n1, x1)
        for name in NAMES:
            if lookup(ab, name) != lookup(ba, name):
                return False
    return True


def check_general_commutativity(trials: int = 300, seed: int = 1) -> bool:
    """Example 43.5: raw structural equality of the two orderings -- the
    chapter shows this fails for a list-based representation."""
    rng = random.Random(seed)
    for _ in range(trials):
        db = random_db(REFERENCE, rng, 5)
        n1, n2 = rng.sample(NAMES, 2)
        x1, x2 = rng.choice(NUMBERS), rng.choice(NUMBERS)
        ab = update(update(db, n1, x1), n2, x2)
        ba = update(update(db, n2, x2), n1, x1)
        if ab != ba:
            return False
    return True


def _demo_database() -> None:
    print("--- 4.2 Telephone Database: ConGu-style random axiom testing ---")

    trial, violation = check_axioms(REFERENCE)
    print(f"  reference implementation: {'OK, no violation in 300 trials' if trial is None else f'FAILED at trial {trial}: {violation}'}")

    trial, violation = check_axioms(BUGGY_IMPLEMENTATION)
    print(f"  Example 43.13-style implementation bug (lookup returns oldest, not most recent):")
    print(f"    caught at trial {trial}: {violation}")

    trial, violation = check_axioms(BUGGY_SPEC)
    print(f"  Example 43.14-style bug (update overwrites in place, losing history):")
    print(f"    caught at trial {trial}: {violation}")

    print(f"  Example 43.4 specialised update commutativity holds? {check_specialised_commutativity()}")
    print(f"  Example 43.5 general update commutativity holds?    {check_general_commutativity()}")


# ===========================================================================
# 2. Ladder Logic / a Pelican Crossing (Sec. 4.3)
# ===========================================================================
#
# State is a 4-tuple of booleans (g, a, r, f): traffic-green, traffic-amber,
# pedestrians-crossing (traffic red), and a flashing clearance phase before
# returning to green. Each is a latch, updated by one "rung" -- a
# definitional extension in the sense of Definition 5, each rung reading
# only the *current* (unprimed) state and the one input `button`.
#
# This is an original, small example built to the chapter's method (Defs.
# 4, 6-8, and Sec. 4.3.4's inductive verification), not a transcription of
# the book's own (much larger) TransitionRelation, which was not fully
# recoverable from the source text.

State = Tuple[bool, bool, bool, bool]  # (g, a, r, f)


def transition(state: State, button: bool) -> State:
    g, a, r, f = state
    g2 = f or (g and not button) or (not g and not a and not r and not f)
    a2 = g and button
    r2 = a
    f2 = r
    return (g2, a2, r2, f2)


def buggy_transition(state: State, button: bool) -> State:
    """A plausible typo: the rung for r' also fires on g (not just a),
    letting the crossing phase overlap with traffic green."""
    g, a, r, f = state
    g2 = f or (g and not button) or (not g and not a and not r and not f)
    a2 = g and button
    r2 = a or g  # BUG: should be just `a`
    f2 = r
    return (g2, a2, r2, f2)


INITIAL_STATE: State = (False, False, False, False)  # Sec. 4.3.1's init procedure
ALL_STATES: List[State] = list(itertools.product([False, True], repeat=4))
INPUTS = (False, True)


def reachable_states(trans: Callable[[State, bool], State], start: State) -> set:
    """The automaton A(TR) of Definition 7, restricted to states reachable
    from `start` (rather than all initial states, since here there's only
    the one PLC-init state)."""
    seen = {start}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        for button in INPUTS:
            s2 = trans(s, button)
            if s2 not in seen:
                seen.add(s2)
                queue.append(s2)
    return seen


def mutual_exclusion_safe(state: State) -> bool:
    """The safety concern from the chapter's introduction (Example 44):
    no two of {green, amber, crossing, flashing} may hold simultaneously."""
    return sum(state) <= 1


def verification_problem(
    trans: Callable[[State, bool], State], start: State, safety: Callable[[State], bool]
) -> Tuple[bool, Optional[State]]:
    """Definition 8, directly: is safety true in every reachable state?
    (Feasible here only because the state space is tiny -- for realistic
    programs one needs the inductive/bounded techniques the book turns to
    next.)"""
    for s in reachable_states(trans, start):
        if not safety(s):
            return False, s
    return True, None


def inductive_verification(
    trans: Callable[[State, bool], State],
    start: State,
    safety: Callable[[State], bool],
    states: List[State] = ALL_STATES,
) -> Tuple[bool, Optional[tuple]]:
    """Sec. 4.3.4: (1) initial states are safe; (2) safety is preserved by
    every transition -- checked over *all* boolean states satisfying
    `safety`, not just the reachable ones. This over-approximation is what
    can make inductive verification report a false positive on a real
    program (Example 44.9) even when the property genuinely holds on all
    reachable states."""
    if not safety(start):
        return False, ("initial-not-safe", start)
    for s in states:
        if not safety(s):
            continue
        for button in INPUTS:
            s2 = trans(s, button)
            if not safety(s2):
                return False, ("induction-step-fails", s, button, s2)
    return True, None


def _label(state: State) -> str:
    names = ["green", "amber", "crossing", "flashing"]
    active = [n for n, on in zip(names, state) if on]
    return "+".join(active) if active else "off"


def _demo_ladder_logic() -> None:
    print("--- 4.3 Ladder Logic: a Pelican Crossing automaton ---")

    reachable = reachable_states(transition, INITIAL_STATE)
    print(f"  reachable states ({len(reachable)}): " + ", ".join(sorted(_label(s) for s in reachable)))

    ok, witness = verification_problem(transition, INITIAL_STATE, mutual_exclusion_safe)
    print(f"  Definition 8 verification problem (mutual exclusion on all reachable states)? {ok}")

    ok, witness = inductive_verification(transition, INITIAL_STATE, mutual_exclusion_safe)
    print(f"  Sec. 4.3.4 inductive verification (over all {len(ALL_STATES)} boolean states)? {ok}")

    print("  now with a one-rung bug (r' also fires on g, not just a):")
    reachable_buggy = reachable_states(buggy_transition, INITIAL_STATE)
    print(f"  reachable states ({len(reachable_buggy)}): " + ", ".join(sorted(_label(s) for s in reachable_buggy)))
    ok, witness = verification_problem(buggy_transition, INITIAL_STATE, mutual_exclusion_safe)
    print(f"  Definition 8 verification problem? {ok}  (witness: {witness and _label(witness)})")
    ok, witness = inductive_verification(buggy_transition, INITIAL_STATE, mutual_exclusion_safe)
    print(f"  inductive verification? {ok}  (witness: {witness})")


# ===========================================================================
# 3. Structuring specifications (Sec. 4.4)
# ===========================================================================


@dataclass(frozen=True)
class Signature:
    sorts: FrozenSet[str]
    ops: FrozenSet[Tuple[str, ...]]  # (name, *arg_sorts, result_sort)
    preds: FrozenSet[Tuple[str, ...]]  # (name, *arg_sorts)

    def __repr__(self) -> str:
        ops = ", ".join(f"{o[0]}:{'x'.join(o[1:-1]) or '()'}->{o[-1]}" for o in sorted(self.ops))
        preds = ", ".join(f"{p[0]}:{'x'.join(p[1:])}" for p in sorted(self.preds))
        return f"sorts {', '.join(sorted(self.sorts))}; ops {ops}; preds {preds}"


def extension(sp: Signature, sorts=frozenset(), ops=frozenset(), preds=frozenset()) -> Signature:
    """Sec. 4.4.1: Sp then <new symbols>."""
    return Signature(sp.sorts | sorts, sp.ops | ops, sp.preds | preds)


def union(sp1: Signature, sp2: Signature) -> Signature:
    """Sec. 4.4.2: Sp1 and Sp2 -- an ordinary set union of signatures, so a
    symbol declared in both ('same name, same thing') appears only once."""
    return Signature(sp1.sorts | sp2.sorts, sp1.ops | sp2.ops, sp1.preds | sp2.preds)


def rename(sp: Signature, mapping: Dict[str, str]) -> Signature:
    """Sec. 4.4.3: Sp with s1 |-> s1', ... -- consistently rename symbols."""

    def r(x: str) -> str:
        return mapping.get(x, x)

    return Signature(
        frozenset(r(s) for s in sp.sorts),
        frozenset(tuple(r(part) for part in op) for op in sp.ops),
        frozenset(tuple(r(part) for part in p) for p in sp.preds),
    )


def _demo_structuring() -> None:
    print("--- 4.4 Structuring specifications: signatures only ---")

    irreflexive = Signature(frozenset({"Elem"}), frozenset(), frozenset({("<", "Elem", "Elem")}))
    transitive = Signature(frozenset({"Elem"}), frozenset(), frozenset({("<", "Elem", "Elem")}))
    print(f"  IrreflexiveRelation: {irreflexive}")
    print(f"  TransitiveRelation:  {transitive}")
    combined = union(irreflexive, transitive)
    print(f"  union (Example 46, 'same name, same thing'): {combined}")
    print(f"  Elem declared once, not twice: {len(combined.sorts) == 1}")

    lists = Signature(
        frozenset({"List"}),
        frozenset({("append", "List", "List", "List"), ("empty", "List")}),
        frozenset(),
    )
    monoid_shape = Signature(
        frozenset({"M"}),
        frozenset({("*", "M", "M", "M"), ("e", "M")}),
        frozenset(),
    )
    renamed = rename(lists, {"List": "M", "append": "*", "empty": "e"})
    print(f"  Lists signature:          {lists}")
    print(f"  renamed (Example 47):     {renamed}")
    print(f"  matches Monoid's shape?   {renamed == monoid_shape}")


if __name__ == "__main__":
    _demo_database()
    print()
    _demo_ladder_logic()
    print()
    _demo_structuring()
