# Specification-Based Testing

Companion notes/code for Chapter 5, "Specification-Based Testing", of
Roggenbach, Cerone, Schlingloff, Schneider & Shaikh, *Formal Methods for
Software Engineering* (Springer, 2022) — see the top-level
[README.md](../README.md) for the course as a whole. (No page range is
cited here — the range given for this chapter matched an earlier chapter's
range exactly, so it looked like a copy-paste artifact; better to omit it
than cite a guessed number.)

`main.py` implements four small toolkits, one per major technique the
chapter covers, each checked against the chapter's own worked example (the
VCR power switch) or a chapter-specific case study. Run it with
`python "main.py"` from this folder (see [Environment](#environment)
below).

## 5.1 The role of testing in software design

Testing and formal verification are **complementary**, not substitutes:
verification compares two mathematical objects (a program and a spec);
testing checks whether a *physical* system matches expectations — you can
verify a sorting algorithm and still ship a payroll program that issues
wrong paychecks, because testing catches integration problems verification
never touches. Definition 1: testing is *systematic experimentation with a
material object to establish its quality*. A chain of causation runs
**error** (human misconception) → **fault** (wrong state in the system) →
**failure** (observable deviation from spec). Testing requires a
*precise* specification — "the system shall never crash" isn't testable;
a formal spec is. The chapter's central axis: **code-based** (white-box)
testing derives test structure from the SUT's source; **specification-
based** (black-box) testing derives it from the spec instead — the
subject of this chapter.

## 5.2 State-based testing

Models reactive systems as **UML state machines** (states, pseudostates,
transitions labelled `trigger[guard]/effect`), worked through a VCR power
switch with three modes (`rec`/`mem`/`play`) nested inside an `on` state
that shares one `up`-transition back to `off` (a composite-state detail
that matters for coverage counting below).

- **5.2.2 Test generation**: a test case is a finite path of
  input/output labels from the initial state. **Algorithm 8** builds a
  coverage-directed suite: BFS the shortest path to every state, then
  emit paths starting with the *most distant* uncovered goal first,
  skipping anything already covered. **Coverage criteria** form a lattice
  by subsumption: `all-transitions` ⊇ `all-states`, `all-transitions` ⊇
  `all-events`, `all-n-transitions` ⊇ `depth-n`. `all-transitions` alone
  can need up to `nˢᵗᵃᵗᵉˢ · mᵉᵛᵉᵂᵗˢ` test cases in the worst case, so
  `depth-n` (n = the model's diameter) is the practical middle ground.
- **5.2.3 Monitoring**: a **test oracle** decides pass/fail for an
  execution trace against a property written in **LTL** over the
  ENV2SUT/SUT2ENV interface labels. Algorithm 7 evaluates LTL by
  unwinding the standard recursive characterizations (`G φ = φ ∧ X(Gφ)`,
  `F φ = φ ∨ X(Fφ)`) directly against the trace — cheaper than full model
  checking, and answering a different question (does *this run* satisfy
  φ?, not does *every* run?). The chapter uses a **weak until** ("unless")
  operator for properties like "a lamp stays lit until up is pressed
  again", precisely because a captured test trace isn't guaranteed to end
  with the switch back at `off`.
- **5.2.4 Coverage in depth**: with cycles in the model, `all-n-
  transitions` can demand infinitely many test cases in the limit, so
  practical suites bound `n`; test-suite *size* is measured by total
  events, cardinality, or input-event count depending on what's
  expensive to execute (resetting the SUT vs. performing a manual input
  vs. just observing an output).

`main.py`'s `all_states_suite()` is a direct implementation of Algorithm
8, run against the VCR switch — it reproduces the book's own all-states
suite **exactly**: `(dn?,100!,dn?,010!,dn?,001!)`. The all-transitions and
decision-coverage suites the book states by example are independently
checked here via a `covered_goal_ids()` helper (crediting the three
`up?`-transitions as *one* coverage goal, matching the composite state's
inherited transition). `eval_ltl()`/`test_oracle()` implement Algorithm 7
with `Next`/`Always`/`Eventually`/`Until`/`WeakUntil`, checked against
simulated VCR traces, including a direct demonstration of why weak-until
is needed (a trace that never presses `up?` still passes).

## 5.3 Conformance testing

Answers "when is a test suite *complete*?" — **sound** (every correct
implementation passes) and **exhaustive** (every incorrect one fails).
Tretmans' **Input-Output Transition Systems** (IOTS, Def. 2) formalize
this with a hierarchy of testing relations, each strictly finer than the
last:

- **Trace preorder** (`im ≤_traces sp`): traces(im) ⊆ traces(sp). Too
  weak alone — an implementation that does *nothing* trivially satisfies
  any specification's trace preorder.
- **`ioconf`**: additionally, after any trace both can perform, im's
  possible outputs are among sp's.
- **`ioco`**: `ioconf` generalized to **suspension traces** — traces that
  may also contain an explicit "quiescence" observation `δ` (the system
  produced no output and none is forthcoming), via a **suspension
  transition system** with a `δ`-self-loop added at every quiescent
  state. `im ioco sp` iff, after every suspension trace `sp` itself can
  perform, `out(im) ⊆ out(sp)` (where `out` includes `δ`). Critically,
  `ioco` only constrains behaviour at traces the *spec* can perform — an
  implementation can do strictly *more* than an under-specified spec
  without breaking conformance, which trace preorder alone cannot express.
- A **test case** for an IOTS is a finite tree (Def. within Sec. 5.3) —
  inputs/outputs swap roles relative to the spec, since the tester
  *sends* what the spec receives and *checks* what the spec produces.
  The set of all such trees derived from a spec is provably complete for
  `ioco`.

`main.py`'s `IOTS`/`out`/`suspension_traces`/`ioco`/`trace_preorder`
reproduce Example 49.4's two central claims: `sp_refined ioco sp_abstract`
holds even though trace preorder in that direction does *not* (refined's
extra behaviour lands outside `sp_abstract`'s own traces, so `ioco`
doesn't penalize it); and adding a spontaneous "battery failure" output to
the abstract spec breaks `ioco` (refined is quiescent exactly where the
modified spec now insists it must be able to shut down) while trace
preorder — blind to quiescence — still holds. The witness trace `ioco`
reports matches this reasoning exactly.

## 5.4 Using algebraic specifications for testing

A second, function-oriented approach (vs. state-oriented Sec. 5.2):
**Gaudel's theory** treats a **ground instance** of a universally
quantified Casl axiom as a test case — e.g. `dim(4, 2001) = 30` from a
days-in-month specification. Key results:

- If specification formulae are restricted to `∀x̄. φ(x̄)` with `φ`
  quantifier-free, the **full ground-instance suite** (every ground
  instance of every axiom) is provably **complete** (Theorem 1) — sound
  by first-order instantiation, exhaustive because the specification's
  intended models are *term-generated*. This directly contradicts
  Dijkstra's "testing shows the presence of bugs, never their absence" —
  under these conditions, passing the full suite genuinely proves
  correctness.
  - A **fundamental testing assumption** underlies this: the SUT's
    functions/predicates must be referentially transparent (same
    arguments → same result, no side effects) — the chapter shows a
    buggy `isLeapYear` with an internal side-effect counterexample.
- The full suite is typically **infinite** (any spec with a constant and
  a self-applicable function has infinitely many ground terms), so
  Gaudel introduces **test hypotheses** to shrink it *without losing
  completeness*, provided the hypothesis is independently justified (not
  itself established by testing):
  - **Regularity hypothesis**: "if φ(x) holds for all x in a subdomain
    D₀, it holds for all x" — lets you exclude a subdomain entirely
    (e.g. `isLeapYear(y)` is `false` for all `y < 1583` by definition, so
    don't bother testing pre-Gregorian years).
  - **Uniformity hypothesis**: "if φ(x) holds for *one* x in D₀, it holds
    for all of D₀" — lets you replace a whole subdomain with a single
    representative (e.g. test `isLeapYear(2000)` once to stand in for
    *every* year divisible by 400).

`main.py`'s `dim`/`is_leap_year` reference implementation and
`run_ground_suite()` reproduce Example 50's testing workflow directly. A
deliberately introduced bug (forgetting the `%400` leap-year exception —
a real, classic bug class) is caught by the full 6,000-case suite
(12 months × 500 years) and *also* by a 48-case suite built from one
representative per uniformity class (Example 50.2's own reasoning) — a
125× reduction that still catches the bug, since the affected class
(years divisible by 400) has a representative in the reduced suite.

## 5.5 Tool support for testing

Testing has many sub-activities beyond execution (planning, design,
development, evaluation, assessment, documentation, lifecycle and tool
management) — most are automatable to some degree, not just execution.
Model-based testing tools typically pair a **modelling/simulation**
component with a **test generator**; a full industrial pipeline links
requirements management → modelling → test generation → test execution →
defect tracking, with traceability threading all the way back to
requirements.

## 5.6 Closing remarks

The chapter's throughline: formal testing needs a **precise, executable
notion of correctness** before "testing" can mean anything rigorous —
whether that's a state machine's coverage criteria, an LTL oracle over
execution traces, an `ioco`-style conformance relation, or ground
instances of algebraic axioms. Each technique trades completeness against
practicality differently: `ioco` gives a complete (but generally infinite)
test suite for reactive conformance; Gaudel's approach can give a
genuinely complete *and*, with justified hypotheses, *finite* suite for
functional specifications — a rare case where testing really can prove
absence of bugs, not just their presence.

## Environment

A local virtual environment lives at the repo root in `.venv/` (Python
3.14, stdlib only — no third-party packages needed for this module).
Activate it from the repo root:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Git Bash
source .venv/Scripts/activate
```

Run the demo (from the repo root):

```bash
python "Specification-Based Testing/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
