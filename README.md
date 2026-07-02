# Formal-Methods-for-Software-Engineering
Languages, Methods, Application Domains

Let's begin with an understanding of the key ingredients of Formal Methods: 
* syntax, 
* semantics 
* method

The syntax is usually given in Backus–Naur-Form; the semantics is mostly presented in either operational,
denotational, or axiomatic style; the method says how to work with the language.

Formal Methods are useful in classical as well as in agile software
development processes. They are used to achieve precision in design documents
and to support various forms of system analysis. International standards
recognise and recommend the use of various Formal Methods. In practise,
Formal Methods require tool support.

## Chapters

Companion notes and runnable Python code for each chapter, each verified
against the book's own worked examples where the chapter's content is
algorithmic. Chapter 9 ("Origins and Development of Formal Methods") is a
historical survey with no companion here.

- [Chapter 1 — Formal Methods](Formal%20Methods/Formal%20Methods.README.md):
  what a Formal Method actually *is* — Definition 1's syntax/semantics/
  method — worked through the chapter's own running case study, regular
  expressions. The companion code implements a regex engine with both a
  denotational semantics (language membership) and an operational
  semantics (compilation to an automaton), verifies they agree, and
  implements the chapter's formal "regular replacement," resolving a
  real Word-vs-Emacs wildcard disagreement the chapter opens with.
- [Chapter 2 — Logics for Software Engineering](Logics%20for%20Software%20Engineering/Logics%20for%20Software%20Engineering.README.md):
  propositional logic, the institutions framework, first- and second-order
  logic, and non-classical (modal/deontic/temporal) logics. The companion
  code is a propositional-logic toolkit (parser, model checker, SAT/
  validity checker) plus a small Kripke-model evaluator for multimodal
  logic, demoed against the chapter's TV-quiz puzzle, car-configuration,
  and web-graph examples.
- [Chapter 3 — The Process Algebra CSP](The%20Process%20Algebra%20CSP/The%20Process%20Algebra%20CSP.README.md):
  CSP syntax, operational and denotational semantics, refinement, and
  deadlock/livelock analysis. The companion code is a bounded-depth CSP
  engine (process AST, firing-rule transitions, a traces model, deadlock
  and refinement checks), demoed against the chapter's ATM, buffer, and
  bistro-deadlock examples, plus a simulation of the Dining Philosophers-
  style Children's Puzzle.
- [Chapter 4 — Algebraic Specification in CASL](Algebraic%20Specification%20in%20CASL/Algebraic%20Specification%20in%20CASL.README.md):
  CASL signatures/axioms, loose model semantics, consistency checking,
  ladder-logic program verification, and CASL's structuring operators.
  The companion code is a reference Telephone Database implementation
  with a ConGu-style random axiom checker (catches both implementation
  and specification bugs), plus a Pelican Crossing ladder-logic automaton
  with reachability and inductive verification.
- [Chapter 5 — Specification-Based Testing](Specification-Based%20Testing/Specification-Based%20Testing.README.md):
  state-based test generation and coverage criteria, LTL runtime
  monitoring, Tretmans' `ioco` conformance theory, and Gaudel's
  ground-instance testing from algebraic specifications. The companion
  code reproduces the book's own VCR-switch test suite exactly, an LTL
  test oracle, an `ioco` conformance checker matching the book's stated
  results, and a days-in-month test suite that catches a real leap-year
  bug with a 125x-reduced test suite.
- [Chapter 6 — Specification and Verification of Normative Documents](Specification%20and%20Verification%20of%20Normative%20Documents/Specification%20and%20Verification%20of%20Normative%20Documents.README.md):
  the contract language `CL` (obligations/prohibitions/permissions with
  reparations) and Definition 1's four kinds of normative conflict. The
  companion code implements a residual-contract semantics and conflict
  checker, verified against all four conflict cases and against the
  book's own cautionary example of a *spurious* conflict caused by
  abstracting away time.
- [Chapter 7 — Formal Methods for Human-Computer Interaction](Formal%20Methods%20for%20Human-Computer%20Interaction/Formal%20Methods%20for%20Human-Computer%20Interaction.README.md):
  short-term memory and closure, automatic vs. deliberate cognitive
  control, and LTL model checking of interactive systems. The companion
  code mechanically reproduces the chapter's central example: the classic
  ATM "forgotten card" post-completion error emerges from one interface
  design and not another, purely as a side effect of the closure
  mechanism.
- [Chapter 8 — Formal Verification of Security Protocols](Formal%20Verification%20of%20Security%20Protocols/Formal%20Verification%20of%20Security%20Protocols.README.md):
  the Dolev-Yao intruder model, the Needham-Schroeder protocol, and
  rank-function correctness proofs. The companion code implements a
  message algebra and mechanically replays Gavin Lowe's man-in-the-middle
  attack step by step — confirmed by running it, which shows the
  intruder genuinely deriving the victim's secret nonce — and shows the
  Needham-Schroeder-Lowe fix defeating the same attack.

## Appendices

- [Appendix A — Syntax of the Logics in this Book](Appendix%20A%20-%20Syntax%20of%20the%20Logics%20in%20this%20Book.md)
- [Appendix B — Language Definition of CSP](Appendix%20B%20-%20Language%20Definition%20of%20CSP.md)
- [Appendix C — Concrete CASL Syntax](Appendix%20C%20-%20Concrete%20CASL%20Syntax.md)

The full contents of all three appendices are duplicated below, in order.

---

## Appendix A — Syntax of the Logics in this Book

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

### A.1 Regular Expressions

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

### A.2 Propositional Logic

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

### A.3 First- and Second-Order Logic

Cross-reference: Chapter 2, Sec. 2.4 (Definitions 8–18).

#### Basic first-order logic

Given a first-order signature Σ (function symbols, relation symbols,
variables), with `∃` the existential quantifier:

```
t ::= x  |  f(t, ..., t)                              (terms)
φ ::= R(t, ..., t)  |  ¬φ  |  φ → φ  |  ∃x. φ          (formulae)
```

Abbreviation: `∀x. φ := ¬∃x. ¬φ` (universal quantifier).

Example: `∀x ∀y ∀z (R(x,y) ∧ R(y,z) → R(x,z))` — transitivity of R.

#### First-order logic with equality

Assuming `=` is not already part of the signature, add `t = t` as an
atomic formula, with the expected semantics (both sides denote the same
element).

Example: `∃x ∃y (¬(x = y) ∧ ∀z (z = x ∨ z = y))` — the universe has
exactly two elements.

#### Many-sorted logic

The universe is structured into sorts S; every function/relation symbol
and variable is assigned a sort, and function/relation arguments must
respect sort constraints.

Example: `∀x:Elem ∀y:Elem (x ≤ y ∨ y ≤ x)` — totality of an order on
sort `Elem`.

#### First-order logic with partiality

A signature with partiality distinguishes total function symbols from
partial ones; the unary predicate `def(t)` states whether `t` is defined.

Example: `def(first(s)) → s ≠ eps` — `first` is defined only for
non-empty sequences.

#### Monadic second-order logic (MSO)

Quantification is allowed over both individual variables and (unary)
predicate variables `X`.

Abbreviation: `∀X. φ := ¬∃X. ¬φ` (universal second-order quantifier).

Example: the principle of mathematical induction, `∀X ((X(0) ∧ ∀x(X(x) →
X(x+1))) → ∀x X(x))`.

### A.4 Non-Classical Logics

Cross-reference: Chapter 2, Sec. 2.5.

#### Modal logic

`◇` is the modal possibility ("diamond") operator.

Abbreviation: `□φ := ¬◇¬φ` (necessity/box).

Example: `◇□p → □◇p`.

#### Multimodal logic

One diamond operator `◇_R` per accessibility relation R.

Abbreviation: `□_R φ := ¬◇_R ¬φ` (multimodal box).

#### Deontic logic

The modal possibility operator is reinterpreted as permission `P`;
nesting of modalities is disallowed.

Abbreviations: `Oφ := ¬P¬φ` (obligation), `Fφ := O¬φ` (prohibition).

#### Linear temporal logic (LTL)

Besides the modal next-operator `X`, LTL has a binary until-operator `U`.

Abbreviations: `Fφ := true U φ` (eventually/sometime), `Gφ := ¬F¬φ`
(globally/always).

---

See also: [Chapter 2 companion notes and code](Logics%20for%20Software%20Engineering/) for a
runnable propositional/modal logic toolkit built directly on these
definitions.

---

## Appendix B — Language Definition of CSP

Reference summary of Appendix B from Roggenbach, Cerone, Schlingloff,
Schneider & Shaikh, *Formal Methods for Software Engineering* (Springer,
2022): the formal grammar, static semantics, operational semantics, and
denotational semantics (traces, failures/divergences, and stable
failures models) of CSP as used throughout the book. For the fully
worked-through, example-driven treatment of this material — with a
runnable CSP engine (process AST, firing-rule transitions, traces,
deadlock and refinement checks) — see [Chapter 3, "The Process Algebra
CSP"](The%20Process%20Algebra%20CSP/).

**A note on sourcing:** this appendix is dense with formal notation —
grammar productions, healthiness-condition formulas, semantic clauses,
and firing-rule premises — nearly all of which is typeset as images/math
markup in the source EPUB and did not survive plain-text extraction.
What follows preserves the appendix's own section structure and every
piece of prose/labelling that *did* survive (operator names, the exact
operator-precedence ordering, healthiness-condition *names* such as T1
or D2, and the semantic-domain definitions given in words), but does
**not** claim to reproduce exact formulas that weren't recoverable. Where
a gap exists, cross-reference to Chapter 3's README is given instead,
since that chapter explains (and this repo's code implements) the same
underlying semantics with worked examples.

### B.1 Syntax

#### B.1.1 Processes

The CSP grammar is defined relative to an alphabet of events Σ and a set
of process names. The book lists the following process constructs (see
Chapter 3, Sec. 3.2.1 for the full example-driven introduction to each):

- `STOP` — deadlock, no firing rule
- `SKIP` — successful termination
- `a → P` — action prefix
- `c?x → P`, `c!e → P` — channel input/output (structured events)
- prefix choice over a set A — has **no** direct CSP‖ (machine-readable
  CSP) counterpart; for finite A it can be simulated via replicated
  external choice
- `P □ Q` — external choice
- `P ⊓ Q` — internal choice
- `P ◁ cond ▷ Q` — conditional, where `cond` is a condition in an
  unspecified "logic of choice" (not fixed by CSP itself)
- `P ; Q` — sequential composition
- `P △ Q` — interrupt
- `P [|A|] Q` — general parallel, requiring that for every event the
  process is willing to engage in that isn't in the synchronisation set,
  a suitable partner relation holds
- `P \ A` — hiding
- `P[[R]]` — renaming, written in CSPm as `P[[a <- b]]`; CSPm offers a
  richer comprehension syntax for complex renamings (see the FDR user
  manual or Roscoe's *The Theory and Practice of Concurrency*, 1998)
- replicated operators over a finite index set I, e.g. `⊟ i:I @ [Ai] Pi`
  (replicated alphabetised parallel, requiring alphabets `Ai` to satisfy
  the same subset discipline as binary alphabetised parallel) and
  replicated choice/parallel over a non-empty index set J
- `CHAOS` — similar to the most-general-livelock process, but additionally
  can never terminate; defined via internal choice and prefixing over all
  of its alphabet

The book deliberately omits, for the sake of a manageable introduction,
constructs such as multi-channel events (transferring multiple values in
one event), linked parallel, and the untimed timeout operator.

#### B.1.2 Operator Precedence

Recovered verbatim from the source (this determines how many brackets a
CSP expression needs): from tightest- to loosest-binding —

1. renaming
2. prefix, guard, and sequential composition
3. interrupt, external choice, internal choice
4. the parallel operators
5. conditional

#### B.1.3 Process Equations

A process equation has the form `N = P`, where `N` is a process name and
`P` is a process term as given by the grammar above (Sec. B.1.1). See
Chapter 3, Sec. 3.4.3 for how recursive process equations are given
semantics via fixed points.

### B.2 Semantics

#### B.2.1 Static Semantics

CSP's static semantics governs variable scope, the relationship between
synchronisation sets and process alphabets, and uniqueness of process
name definitions:

- CSP distinguishes **static** variables (bound by replicated operators
  and by process names on the left-hand side of an equation; unaffected
  by process termination) from **dynamic** variables (bound by prefix
  choice and channel input; their binding lasts until the process
  terminates).
- `P [|A|] Q` is well-formed if the alphabet of `P` is a subset of `A`
  and the alphabet of `Q` is a subset of the corresponding set for `Q`.
- A replicated alphabetised parallel is well-formed if, for every index
  `i`, the alphabet of `Pi` is a subset of the corresponding `Ai`.
- A system of process equations is well-formed if there is exactly one
  equation per occurring process name.

#### B.2.2 Syntactic Sugar

Several operators are semantically just syntactic sugar over a smaller
core language: channels themselves are syntactic sugar over plain
events, and several operators "expand directly" into combinations of
others (the book gives the exact expansions in a figure not recoverable
here — see Chapter 3's own discussion of interleaving as general
parallel with an empty synchronisation set, and synchronous parallel as
general parallel with the synchronisation set equal to the full
alphabet, both of which follow this same pattern). Replicated operators
are defined **inductively** on the size of their finite index set `I`
(base case for `|I| = 1`, inductive case combining the head element with
the replicated operator over the rest) — the book notes one subtlety:
the "neutral element" convention it adopts for the empty-index-set case
of replicated general parallel matches the FDR documentation and CSP's
own algebraic laws, but not FDR's actual runtime behaviour, which
differs.

Prefix choice and replicated internal choice are explicitly **not**
syntactic sugar — they are part of the CSP core language, since both
allow infinite branching.

#### B.2.3 Core Language

The appendix isolates a minimal core language from which the rest is
derived (the specific figure delineating "core" vs. "derived" operators
did not survive extraction). In practice, `STOP`, action prefix, external
and internal choice, general parallel, hiding, renaming, and prefix
choice/replicated internal choice (for infinite branching) form the
irreducible core that Chapter 3's own operational-semantics discussion
(Sec. 3.2.2) and this repo's [CSP toolkit](The%20Process%20Algebra%20CSP/main.py)
build directly on.

### B.3 Operational Semantics

Following Roscoe's *The Theory and Practice of Concurrency* (1998), the
appendix's transition-system labels are implicitly typed: `a` ranges
over the alphabet Σ, `b` over observable events (Σ ∪ {✓}), and `x` over
non-terminating events (Σ ∪ {τ}). A distinguished state Ω represents "a
process after termination," reachable only via a ✓-labelled transition —
this is what lets the parallel operator's firing rules treat termination
uniformly.

Firing rules are given (labels only survived extraction; the rules
themselves are exactly what Chapter 3's `transitions()` function and its
`STOP`/`SKIP`/`Prefix`/`ExtChoice`/`IntChoice`/`Seq`/`GenParallel`/
`Hide`/`Rename`/`Rec` dispatch arms implement, one per construct):
`STOP` (no rule), `SKIP` (terminates via ✓), process names, action
prefix, prefix choice, external choice, internal choice, conditional,
sequential composition, interrupt, general parallel, hiding, relational
renaming, and replicated internal choice.

### B.4 Denotational Semantics

Standard notations used throughout: Σ (alphabet of events), Σ✓ (Σ
extended with the termination event ✓), Σ*✓ (all non-terminating traces
over Σ), and (Σ*✓)⟨✓⟩ (all "interesting" traces — both non-terminating
and terminating ones).

#### B.4.1 The Traces Model (T)

The denotation of a process P over alphabet Σ is a set of traces T ⊆
(Σ*✓)⟨✓⟩ satisfying healthiness condition **T1**: `⟨⟩ ∈ T`, and T is
prefix-closed. The domain forms a complete partial order with a bottom
element under trace-set inclusion. Refinement: `Q ⊑_T P` iff `traces(Q)
⊆ traces(P)`. Per the book's own wording, one process "refines all
processes" and a (different) process "is the least refined process" —
see Chapter 3's README (Sec. 3.4.1) for the fully worked-out identification
of these two processes (`STOP` and the most-general-livelock process,
respectively) and why the direction of "most/least refined" can look
counter-intuitive at first.

#### B.4.2 The Failures/Divergences Model (N)

The denotation of P is a pair `(F, D)` of failures and divergences.
Healthiness conditions are named F1–F4 (on failures) and D1–D3 (on
divergences) — their exact formulas didn't survive extraction; Chapter
3's README (Sec. 3.4.1) explains the two that matter most in practice:
D1 (divergences are extension-closed) and D2 (divergent traces have all
possible failures). The domain is a complete partial order with bottom
element for finite alphabets.

#### B.4.3 The Stable Failures Model (F)

The denotation of P is a pair `(T, F)` of traces and *stable* failures
(ignoring divergence). Healthiness conditions T1–T3 and F2–F4 are named;
see Chapter 3's README for the two the book explains in prose (T2, T3)
and for how this model relates to N (they agree exactly on
divergence-free processes — Chapter 3's Theorem 7).

---

See also: [Chapter 3 companion notes and code](The%20Process%20Algebra%20CSP/) for a
runnable, bounded-depth CSP engine implementing this operational
semantics and traces model directly, checked against the chapter's own
worked examples (the ATM, the bistro deadlock story, the `BUFF` buffer).

---

## Appendix C — Concrete CASL Syntax

Reference summary of Appendix C from Roggenbach, Cerone, Schlingloff,
Schneider & Shaikh, *Formal Methods for Software Engineering* (Springer,
2022): a grammar for the concrete syntax of the sublanguage of CASL used
in the book. For the full authoritative grammar, see Peter D. Mosses'
*CASL Reference Manual* (Springer, 2004), which this appendix follows
closely while resolving chain rules, adding a start symbol, and
simplifying the grammar of terms and lexical syntax. For the
example-driven treatment of what this grammar actually expresses, with a
runnable reference implementation and a ConGu-style random axiom
checker, see [Chapter 4, "Algebraic Specification in
CASL"](Algebraic%20Specification%20in%20CASL/).

**A note on sourcing:** the appendix's actual grammar productions (the
BNF/EBNF rules for `C.1`–`C.4`) are typeset as figures/images in the
source EPUB and did not survive plain-text extraction — only the
appendix's own *notational conventions* and section structure did. Rather
than guess at the missing productions, this file documents the
conventions the book states explicitly and points to the CASL Reference
Manual and Chapter 4's own worked examples (Sec. 4.2.1's `Database-
Signature`, `sorts`/`ops`/`preds` declarations) for the concrete grammar
itself.

### Notational Conventions (stated explicitly in the appendix)

- **Nonterminal symbols** are written as uppercase words, possibly
  hyphenated, e.g. `SORT`, `BASIC-SPEC`.
- **Terminal symbols** are written either as lowercase words (e.g.
  `free`, `op`) or as special character sequences enclosed in double
  quotes (e.g. `"."`, `"::="`).
- **Optional symbols** are followed by a slash, e.g. `end/`; optional
  terminal alternatives are also slash-separated, e.g. `sort/sorts`.
- **Alternative sequences** are separated by vertical bars, e.g.
  `true | false`.
- **Repetitions** are indicated by an ellipsis `...` between symbols;
  ellipses are also used at the end of an alternative to indicate
  omissions from the (simplified) grammar presented here.
- **Production rules** are written as `NONTERMINAL ::= alternative |
  alternative | ...`.
- The lexical syntax of identifiers is given by the nonterminal `WORD`:
  it must start with a letter and must not be a reserved keyword.

The appendix's grammar offers only minimal structuring support; for the
concrete syntax of the full structuring operations (extension, union,
renaming, libraries, parameterisation, hiding — see Chapter 4, Sec. 4.4),
the CASL Reference Manual is the authoritative source.

### C.1 Specifications

The top-level grammar for a CASL specification (`spec NAME = BASIC-SPEC
end`, with `then`/`and` for extension/union — see Chapter 4, Sec.
4.4.1–4.4.2 for the worked examples this grammar underpins). The
appendix's own production rules for this section were not recoverable
from the source; see Chapter 4's [`main.py`](Algebraic%20Specification%20in%20CASL/main.py)
for a signature-level (`extension`/`union`/`rename`) implementation of
the corresponding semantics.

### C.2 Signature Declarations

Covers the concrete syntax for declaring sorts (`sort`/`sorts`), total
and partial operations (`op`/`ops`, with `->` vs. `->?` for partiality —
see Chapter 4, Example 43.1), and predicates (`pred`/`preds`). Compare
against the worked signature in Chapter 4's Telephone Database example:

```
spec Database-Signature =
  sorts Database, Name, Number
  ops   initial : Database;
        update : Database × Name × Number -> Database;
        lookUp : Database × Name ->? Number;
        delete : Database × Name -> Database
  preds isEmpty : Database
end
```

### C.3 Formulae

Extends `BASIC-ITEMS` with constructs for writing axioms — quantified
first-order formulae over the declared signature, following `%(label)%`
conventions for naming axioms (see Chapter 4, Example 43.2's `%(name_
found)%`-style labelled axioms) and the `%implies`/`%cons`/`%def`
annotations for expressing proof obligations about an extension (Chapter
4, Sec. 4.3.2, Definition 5).

### C.4 Sort Generation Constraints

Extends `BASIC-ITEMS` with the `generated`/`free` type constructs (see
Chapter 4, Example 43.7's `free type` usage) — syntactic sugar for the
second-order term-generatedness properties discussed in Chapter 2, Sec.
2.4.2 (Definitions 17–18).

---

See also: [Chapter 4 companion notes and code](Algebraic%20Specification%20in%20CASL/) for a
worked reference implementation of a CASL specification (the Telephone
Database), a ConGu-style random axiom checker, and a signature-level
implementation of CASL's structuring operators.
