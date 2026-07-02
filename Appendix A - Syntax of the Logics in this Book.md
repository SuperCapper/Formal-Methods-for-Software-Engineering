# Appendix A — Syntax of the Logics in this Book

Reference summary of Appendix A from Roggenbach, Cerone, Schlingloff,
Schneider & Shaikh, *Formal Methods for Software Engineering* (Springer,
2022): a quick-reference syntax sheet for the logics and formalisms used
throughout the book. The appendix itself is explicitly a *terse
cross-reference* to material explained in full in the main chapters —
above all [Chapter 2, "Logics for Software Engineering"](Logics%20for%20Software%20Engineering/), whose
companion notes and runnable code cover propositional logic, first- and
second-order logic, and modal/deontic/temporal logic in depth, with a
working propositional/modal-logic toolkit you can run.

**A note on sourcing:** the appendix's own worked "Example formulae" for
each logic are typeset as inline math and did not survive plain-text
extraction from the source EPUB — only the section structure, the named
abbreviations, and Appendix A.1's fully-prose regular-expression examples
did. The syntax definitions below are reconstructed in standard notation,
cross-checked against Chapter 2's own (fully recovered) definitions where
they overlap, rather than a verbatim transcription of the appendix's own
missing example lines.

The symbol `:=` stands for "equal by definition" throughout, matching the
book's own convention (rendered there as `≡`).

## A.1 Regular Expressions

Given a finite alphabet Σ of letters:

```
E ::= a  (a ∈ Σ)  |  ε  |  E.E  |  E+E  |  E*
```

Abbreviations:

- `ε` — the empty word
- `E+` — one or more repetitions of `E` (:= `E.E*`)
- `.` (the "any letter" wildcard) — any single letter of Σ
- `Σ*` — any word
- `E?` — maybe one `E` (:= `E + ε`)
- `E^n` (n ≥ 0) — exactly n repetitions of `E`
- `E^{m,n}` (0 ≤ m ≤ n) — at least m and at most n repetitions of `E`

Examples (from the book):

- `a.b*` — a, followed by zero or more b's
- `a+` — one or more a's (equivalently `a.a*`)
- `Σ.Σ.Σ` — any three-letter word

## A.2 Propositional Logic

Cross-reference: Chapter 2, Sec. 2.2 (Definition 1) — see the [companion
code](Logics%20for%20Software%20Engineering/main.py) for a working parser,
model checker, and SAT/validity checker built directly from this grammar.

Given a finite set Σ of proposition symbols (`⊥` is "falsum", `→` is
implication):

```
φ ::= p  (p ∈ Σ)  |  ⊥  |  φ → φ
```

Abbreviations:

- `¬φ := φ → ⊥` (negation)
- `⊤ := ¬⊥` (verum)
- `φ ∨ ψ := ¬φ → ψ` (disjunction)
- `φ ∧ ψ := ¬(φ → ¬ψ)` (conjunction)
- `φ ↔ ψ := (φ → ψ) ∧ (ψ → φ)` (equivalence)
- `φ ⊕ ψ := ¬(φ ↔ ψ)` (exclusive-or)
- `⋁ᵢφᵢ`, `⋀ᵢφᵢ` — (finite) choice/conjunction over an indexed family

Example formulae: `p ∨ ¬p` is a tautology; `p ∧ ¬p` is unsatisfiable.

## A.3 First- and Second-Order Logic

Cross-reference: Chapter 2, Sec. 2.4 (Definitions 8–18).

### Basic first-order logic

Given a first-order signature Σ (function symbols, relation symbols,
variables), with `∃` the existential quantifier:

```
t ::= x  |  f(t, ..., t)                              (terms)
φ ::= R(t, ..., t)  |  ¬φ  |  φ → φ  |  ∃x. φ          (formulae)
```

Abbreviation: `∀x. φ := ¬∃x. ¬φ` (universal quantifier).

Example: `∀x ∀y ∀z (R(x,y) ∧ R(y,z) → R(x,z))` — transitivity of R.

### First-order logic with equality

Assuming `=` is not already part of the signature, add `t = t` as an
atomic formula, with the expected semantics (both sides denote the same
element).

Example: `∃x ∃y (¬(x = y) ∧ ∀z (z = x ∨ z = y))` — the universe has
exactly two elements.

### Many-sorted logic

The universe is structured into sorts S; every function/relation symbol
and variable is assigned a sort, and function/relation arguments must
respect sort constraints.

Example: `∀x:Elem ∀y:Elem (x ≤ y ∨ y ≤ x)` — totality of an order on
sort `Elem`.

### First-order logic with partiality

A signature with partiality distinguishes total function symbols from
partial ones; the unary predicate `def(t)` states whether `t` is defined.

Example: `def(first(s)) → s ≠ eps` — `first` is defined only for
non-empty sequences.

### Monadic second-order logic (MSO)

Quantification is allowed over both individual variables and (unary)
predicate variables `X`.

Abbreviation: `∀X. φ := ¬∃X. ¬φ` (universal second-order quantifier).

Example: the principle of mathematical induction, `∀X ((X(0) ∧ ∀x(X(x) →
X(x+1))) → ∀x X(x))`.

## A.4 Non-Classical Logics

Cross-reference: Chapter 2, Sec. 2.5.

### Modal logic

`◇` is the modal possibility ("diamond") operator.

Abbreviation: `□φ := ¬◇¬φ` (necessity/box).

Example: `◇□p → □◇p`.

### Multimodal logic

One diamond operator `◇_R` per accessibility relation R.

Abbreviation: `□_R φ := ¬◇_R ¬φ` (multimodal box).

### Deontic logic

The modal possibility operator is reinterpreted as permission `P`;
nesting of modalities is disallowed.

Abbreviations: `Oφ := ¬P¬φ` (obligation), `Fφ := O¬φ` (prohibition).

### Linear temporal logic (LTL)

Besides the modal next-operator `X`, LTL has a binary until-operator `U`.

Abbreviations: `Fφ := true U φ` (eventually/sometime), `Gφ := ¬F¬φ`
(globally/always).

---

See also: [Chapter 2 companion notes and code](Logics%20for%20Software%20Engineering/) for a
runnable propositional/modal logic toolkit built directly on these
definitions.
