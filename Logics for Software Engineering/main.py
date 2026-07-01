"""Companion code for Chapter 2, "Logics for Software Engineering"
(Roggenbach et al., *Formal Methods for Software Engineering*, pgs. 85-157).

Two small logic toolkits, each mirroring the chapter's own definitions:

1. Propositional logic (Sec. 2.2): formulae, the validation relation |=,
   satisfiability/validity checking, truth tables, and a tiny parser.
2. Multimodal / Kripke logic (Sec. 2.5.1): worlds, accessibility relations,
   and box/diamond evaluation.

Run this file directly to see both toolkits applied to the chapter's own
running examples (the TV quiz puzzle, car configuration, and a small
web-graph modal model).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import Dict, FrozenSet, Iterator, Optional, Set


# ===========================================================================
# 1. Propositional logic (Sec. 2.2, Definitions 1-3)
# ===========================================================================


class Formula:
    def __and__(self, other: "Formula") -> "Formula":
        return And(self, other)

    def __or__(self, other: "Formula") -> "Formula":
        return Or(self, other)

    def __invert__(self) -> "Formula":
        return Not(self)

    def implies(self, other: "Formula") -> "Formula":
        return Implies(self, other)

    def iff(self, other: "Formula") -> "Formula":
        return Iff(self, other)


@dataclass(frozen=True)
class Const(Formula):
    value: bool

    def __repr__(self) -> str:
        return "true" if self.value else "false"


@dataclass(frozen=True)
class Var(Formula):
    name: str

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Not(Formula):
    inner: Formula

    def __repr__(self) -> str:
        return f"~{self.inner!r}"


@dataclass(frozen=True)
class And(Formula):
    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return f"({self.left!r} & {self.right!r})"


@dataclass(frozen=True)
class Or(Formula):
    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return f"({self.left!r} | {self.right!r})"


@dataclass(frozen=True)
class Implies(Formula):
    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return f"({self.left!r} -> {self.right!r})"


@dataclass(frozen=True)
class Iff(Formula):
    left: Formula
    right: Formula

    def __repr__(self) -> str:
        return f"({self.left!r} <-> {self.right!r})"


Model = Dict[str, bool]


def proposition_symbols(f: Formula) -> FrozenSet[str]:
    if isinstance(f, Const):
        return frozenset()
    if isinstance(f, Var):
        return frozenset({f.name})
    if isinstance(f, Not):
        return proposition_symbols(f.inner)
    if isinstance(f, (And, Or, Implies, Iff)):
        return proposition_symbols(f.left) | proposition_symbols(f.right)
    raise TypeError(f"unknown formula node: {f!r}")


def evaluate(f: Formula, model: Model) -> bool:
    """Model checking: decide `model |= f` (Definition 2)."""
    if isinstance(f, Const):
        return f.value
    if isinstance(f, Var):
        return model[f.name]
    if isinstance(f, Not):
        return not evaluate(f.inner, model)
    if isinstance(f, And):
        return evaluate(f.left, model) and evaluate(f.right, model)
    if isinstance(f, Or):
        return evaluate(f.left, model) or evaluate(f.right, model)
    if isinstance(f, Implies):
        return (not evaluate(f.left, model)) or evaluate(f.right, model)
    if isinstance(f, Iff):
        return evaluate(f.left, model) == evaluate(f.right, model)
    raise TypeError(f"unknown formula node: {f!r}")


def all_models(symbols) -> Iterator[Model]:
    """Enumerate all 2^n models over the given proposition symbols."""
    ordered = sorted(symbols)
    for values in product([False, True], repeat=len(ordered)):
        yield dict(zip(ordered, values))


def is_satisfiable(f: Formula) -> bool:
    """Brute-force SAT (Sec. 2.2.3, 'Propositional Satisfiability')."""
    symbols = proposition_symbols(f)
    if not symbols:
        return evaluate(f, {})
    return any(evaluate(f, m) for m in all_models(symbols))


def is_valid(f: Formula) -> bool:
    """f is a tautology iff ~f is unsatisfiable (Definition 3)."""
    return not is_satisfiable(Not(f))


def find_model(f: Formula) -> Optional[Model]:
    """Return a satisfying model for f, or None if f is unsatisfiable."""
    symbols = proposition_symbols(f)
    if not symbols:
        return {} if evaluate(f, {}) else None
    for m in all_models(symbols):
        if evaluate(f, m):
            return m
    return None


def entails(premises: Formula, conclusion: Formula) -> bool:
    """Sigma |= phi: every model of the premises also satisfies phi."""
    return is_valid(Implies(premises, conclusion))


def truth_table(f: Formula) -> None:
    symbols = sorted(proposition_symbols(f))
    print(" | ".join(symbols + [repr(f)]))
    for m in all_models(symbols):
        row = [str(m[s]) for s in symbols] + [str(evaluate(f, m))]
        print(" | ".join(row))


# --- A small recursive-descent parser -------------------------------------
#
# Grammar (weakest to strongest binding), matching the abbreviations
# introduced below Definition 1:
#   iff     := implies ("<->" implies)*
#   implies := or ("->" implies)?          (right-associative)
#   or      := and ("|" and)*
#   and     := not ("&" not)*
#   not     := "~" not | atom
#   atom    := "(" iff ")" | "true" | "false" | IDENT

_TOKEN_RE = re.compile(r"<->|->|&|\||~|\(|\)|[A-Za-z_][A-Za-z0-9_]*")


def _tokenize(text: str) -> list:
    return _TOKEN_RE.findall(text)


class _Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> Formula:
        f = self._iff()
        if self._peek() is not None:
            raise SyntaxError(f"unexpected token: {self._peek()!r}")
        return f

    def _iff(self) -> Formula:
        left = self._implies()
        while self._peek() == "<->":
            self._advance()
            left = Iff(left, self._implies())
        return left

    def _implies(self) -> Formula:
        left = self._or()
        if self._peek() == "->":
            self._advance()
            return Implies(left, self._implies())
        return left

    def _or(self) -> Formula:
        left = self._and()
        while self._peek() == "|":
            self._advance()
            left = Or(left, self._and())
        return left

    def _and(self) -> Formula:
        left = self._not()
        while self._peek() == "&":
            self._advance()
            left = And(left, self._not())
        return left

    def _not(self) -> Formula:
        if self._peek() == "~":
            self._advance()
            return Not(self._not())
        return self._atom()

    def _atom(self) -> Formula:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("unexpected end of formula")
        if tok == "(":
            self._advance()
            f = self._iff()
            if self._advance() != ")":
                raise SyntaxError("expected ')'")
            return f
        self._advance()
        if tok == "true":
            return Const(True)
        if tok == "false":
            return Const(False)
        return Var(tok)


def parse(text: str) -> Formula:
    """Parse strings like ``"p & (q -> ~r)"`` into a Formula."""
    return _Parser(_tokenize(text)).parse()


# ===========================================================================
# 2. Multimodal / Kripke logic (Sec. 2.5.1, Definitions 27-28)
# ===========================================================================


@dataclass(frozen=True)
class Box:
    """[R] f -- f holds in every R-successor world."""

    relation: str
    inner: object


@dataclass(frozen=True)
class Diamond:
    """<R> f -- f holds in some R-successor world."""

    relation: str
    inner: object


class KripkeModel:
    """A (multi)modal frame plus a valuation (Definition 27).

    worlds:     the set of possible worlds.
    relations:  relation name -> set of (world, world) accessibility edges.
    valuation:  proposition name -> set of worlds where it holds.
    """

    def __init__(self, worlds: Set[str], relations: Dict[str, Set[tuple]], valuation: Dict[str, Set[str]]):
        self.worlds = worlds
        self.relations = relations
        self.valuation = valuation

    def successors(self, relation: str, world: str) -> Set[str]:
        return {w2 for (w1, w2) in self.relations.get(relation, set()) if w1 == world}


def eval_modal(f, model: KripkeModel, world: str) -> bool:
    """Model checking for multimodal logic (Definition 28)."""
    if isinstance(f, Const):
        return f.value
    if isinstance(f, Var):
        return world in model.valuation.get(f.name, set())
    if isinstance(f, Not):
        return not eval_modal(f.inner, model, world)
    if isinstance(f, And):
        return eval_modal(f.left, model, world) and eval_modal(f.right, model, world)
    if isinstance(f, Or):
        return eval_modal(f.left, model, world) or eval_modal(f.right, model, world)
    if isinstance(f, Implies):
        return (not eval_modal(f.left, model, world)) or eval_modal(f.right, model, world)
    if isinstance(f, Iff):
        return eval_modal(f.left, model, world) == eval_modal(f.right, model, world)
    if isinstance(f, Box):
        return all(eval_modal(f.inner, model, w2) for w2 in model.successors(f.relation, world))
    if isinstance(f, Diamond):
        return any(eval_modal(f.inner, model, w2) for w2 in model.successors(f.relation, world))
    raise TypeError(f"unknown formula node: {f!r}")


def holds_everywhere(f, model: KripkeModel) -> bool:
    """m |= f, i.e. f is universally valid in the model (holds at every world)."""
    return all(eval_modal(f, model, w) for w in model.worlds)


# ===========================================================================
# Demo: the chapter's own running examples
# ===========================================================================


def _demo_quiz_puzzle() -> None:
    """Sec. 2.1: the TV quiz show puzzle with three baskets."""
    print("--- 2.1 TV quiz puzzle ---")
    left, middle, right = Var("prize_left"), Var("prize_middle"), Var("prize_right")

    # Exactly one basket holds the prize.
    exactly_one = (
        (left | middle | right)
        & Not(left & middle)
        & Not(left & right)
        & Not(middle & right)
    )
    # 1. Either the prize is in the middle basket, or the right basket is empty.
    fact1 = middle | Not(right)
    # 2. If the prize is not in the left basket, then it is not in the middle.
    fact2 = Implies(Not(left), Not(middle))

    constraints = exactly_one & fact1 & fact2
    solutions = [m for m in all_models(proposition_symbols(constraints)) if evaluate(constraints, m)]
    print(f"satisfying models: {solutions}")
    for basket, prop in [("left", "prize_left"), ("middle", "prize_middle"), ("right", "prize_right")]:
        forced = all(m[prop] for m in solutions)
        print(f"  {basket} basket forced to hold the prize? {forced}")


def _demo_car_configuration() -> None:
    """Sec. 2.2.1: car configuration satisfiability (Example 18.3)."""
    print("--- 2.2.1 Car configuration ---")
    motor_59kw = Var("motor_59kW")
    gearshift_automatic = Var("gearshift_automatic")

    # Manufacturer constraint: no automatic gearshift with the 59kW motor.
    constraint = Not(motor_59kw & gearshift_automatic)

    bad_request = motor_59kw & gearshift_automatic & constraint
    good_request = motor_59kw & Not(gearshift_automatic) & constraint

    print(f"customer wants 59kW + automatic -> satisfiable? {is_satisfiable(bad_request)}")
    print(f"customer wants 59kW + manual    -> satisfiable? {is_satisfiable(good_request)}")


def _demo_tautologies() -> None:
    print("--- 2.2.2 Tautology / entailment checks ---")
    p = Var("p")
    print(f"p | ~p is valid: {is_valid(p | ~p)}")
    print(f"p & ~p is satisfiable: {is_satisfiable(p & ~p)}")
    print(f"parsed 'p -> (q -> p)' is valid: {is_valid(parse('p -> (q -> p)'))}")


def _demo_web_graph() -> None:
    """Sec. 2.5.1, Example 32: a tiny "world wide web" Kripke model."""
    print("--- 2.5.1 Multimodal web-graph model ---")
    home, hobby, work = "home", "hobby", "work"
    model = KripkeModel(
        worlds={home, hobby, work},
        relations={"link": {(home, hobby), (hobby, home), (home, work), (work, work)}},
        valuation={"homepage": {home}},
    )

    no_dangling = Or(Diamond("link", Var("homepage")), Diamond("link", Diamond("link", Var("homepage"))))
    for world in sorted(model.worlds):
        print(f"  can reach homepage within two links from {world}? {eval_modal(no_dangling, model, world)}")


if __name__ == "__main__":
    _demo_quiz_puzzle()
    print()
    _demo_car_configuration()
    print()
    _demo_tautologies()
    print()
    _demo_web_graph()
