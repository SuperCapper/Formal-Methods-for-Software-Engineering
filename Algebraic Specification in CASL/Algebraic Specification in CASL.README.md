# Algebraic Specification in CASL

Companion notes/code for Chapter 4, "Algebraic Specification in CASL", of
Roggenbach, Cerone, Schlingloff, Schneider & Shaikh, *Formal Methods for
Software Engineering* (Springer, 2022) — see the top-level
[README.md](../README.md) for the course as a whole.

`main.py` implements three small toolkits mirroring the chapter's own
running examples: a Telephone Database with ConGu-style random axiom
testing (§4.2), a Ladder Logic / Pelican Crossing automaton with
reachability and inductive verification (§4.3), and Casl's signature
structuring operators (§4.4). Run it with `python "main.py"` from this
folder (see [Environment](#environment) below).

## 4.1 Introduction

Algebraic specification is **property-oriented**, not model-oriented (see
Sec. 1.2.3): rather than describing *how* to build something, you state
*axioms* it must satisfy — like describing a smartphone to a generous aunt
by its features, not its internals. The semantics of a specification is
the collection of all things ("models") satisfying those axioms — its
**model class**. Adding axioms narrows that pool; narrow it too far and
the pool goes empty (an **inconsistent** specification). Casl's logic is
`SubPCFOL=` (FOL + subsorting + partiality + sort-generation constraints +
equality); this chapter sticks to `PCFOL=` (no subsorting) — see §2.4.3
for the underlying logic itself.

## 4.2 A first example: the Telephone Database

Walks a single example through a full "invent & verify" lifecycle:

- **4.2.1 Modelling**: a **signature** classifies the domain (sorts
  `Database`, `Name`, `Number`; total/partial ops `initial`, `update`,
  `lookUp`, `delete`; predicate `isEmpty`), then **axioms** (PCFOL
  formulae) pin down behaviour — e.g. `lookUp` after `update` returns the
  just-stored number if the name matches, otherwise falls through to the
  earlier entries; `delete` recursively strips *all* matching entries.
  Casl's **model semantics** is exactly the model class of Chapter 2's
  institution framework: `Mod(sp) = {M : M ⊨ Ax(sp)}` — loose semantics,
  since nothing forces a *unique* model. (A digression on classes vs. sets
  and Russell's paradox explains why "the collection of all models" is
  technically a *class*, not a set.)
- **4.2.2 Validating**: populate the spec with concrete constants
  (`Hugo`, `Erna`, ...) and check expected properties are *provable
  consequences* (`%implies`) using a theorem prover (SPASS, via the Hets
  tool). Four possible outcomes for a candidate property φ against a spec:
  undetermined (needs more axioms either way), confirmed consequence,
  refuted (your axioms are wrong), or the spec itself is inconsistent.
  Example 43.5 is a genuinely **undetermined** property (general update
  commutativity) — true for a map-based model, false for a list-based one
  — showing the axioms deliberately under-specify the data representation.
- **4.2.3 Consistency checking**: a spec is consistent iff its model
  class is non-empty (Def. 3) — provable by manually exhibiting one model
  (a small finite algebra), or automatically via a Casl `view` that a
  hand-encoded model satisfies the spec's axioms.
- **4.2.4 Testing Java implementations**: **ConGu** does *random testing*
  of a Java SUT against a Casl-like spec via runtime monitoring — sound
  (a reported error is real) but incomplete (silence isn't a proof).
  Concrete implementation bugs (Example 43.13: `lookup` scanning
  oldest-first) and *specification* bugs (Example 43.14: a missing
  negation making axioms contradictory) are both within reach of random
  testing.

`main.py`'s `initial/update/lookup/delete/is_empty` are a direct
reference implementation of the axioms; `check_axioms()` is a from-scratch
ConGu-style random-runner reproducing this workflow — it passes cleanly
against the reference implementation, and catches *both* an
Example-43.13-style implementation bug and an Example-43.14-style
specification bug within a handful of trials. `check_specialised_
commutativity()` / `check_general_commutativity()` reproduce Examples 43.4
and 43.5 exactly: swapping two updates for different names is invisible to
`lookUp` (holds), but changes the raw list representation (fails) — a
concrete, runnable instance of the "four possibilities" table in §4.2.2.

## 4.3 Verification of Ladder Logic programs

A propositional-logic case study on **Programmable Logic Controllers**
(PLCs), worked through a Pelican crossing:

- **4.3.1-4.3.2**: a PLC loops `read input → compute next state → write
  output`. **Ladder Logic** (IEC 61131) is, mathematically, a restricted
  fragment of propositional logic: each *rung* defines one *primed*
  (next-cycle) variable in terms of *current* (unprimed) ones only — a
  **definitional extension** (Def. 5) in Casl's structuring sense.
  Definition 4 formalizes the three syntactic conditions that make this
  well-formed (every rung defines exactly one fresh primed variable; no
  rung depends on another rung's primed variable). Because of this shape,
  **Theorem 1**: a Ladder Logic program is *always* consistent — unlike,
  e.g., the B method, where you must separately prove the transition
  axioms don't contradict each other.
- **4.3.3**: the associated **automaton** (Def. 6-7) has valuations of all
  variables as states, the transition relation as edges, and "all state
  variables false" as (one of, possibly several) the initial state(s) —
  input variables are left free.
- **4.3.4**: the **verification problem** (Def. 8) asks whether a safety
  formula holds in every *reachable* state. Exhaustive reachability
  analysis doesn't scale, so the chapter uses **inductive verification**:
  (1) check initial states are safe, (2) check safety is preserved by one
  transition step — but checked over *every* state satisfying the safety
  formula, not just the reachable ones. This over-approximation makes
  inductive verification computationally cheap (≤2 prover calls) but
  prone to **false positives**: Example 44.9 shows a real safety property
  that holds on all reachable states yet fails this over-approximate
  check, fixed in Example 44.10 by strengthening the check with a
  separately-verified **invariant** restricting attention to plausible
  states.

`main.py` builds an original (not transcribed — the book's full
`TransitionRelation` wasn't recoverable from the extracted source text)
but methodologically faithful Pelican-crossing automaton: four latches
(green/amber/crossing/flashing), one rung each, one input (`button`).
`reachable_states()` implements Def. 6-7 via BFS; `verification_problem()`
implements Def. 8 directly (feasible since the state space is tiny);
`inductive_verification()` implements §4.3.4's over-approximate check. On
the correct transition relation, both checks agree the crossing is safe
(mutual exclusion of the four phases) — a valid outcome in its own right
(mirroring Example 44.8's direct success, rather than 44.9's false
positive; this toy automaton happens to be well-behaved enough not to
need an invariant). A second, deliberately bugged transition relation (one
rung fires on the wrong current-state variable, letting the pedestrian
crossing phase overlap with traffic green) is caught by *both* checks —
demonstrating verification catching a genuine, safety-critical design
error, arguably the chapter's central practical point.

## 4.4 Structuring specifications

Casl's structuring language is "institution-independent" (Sec. 2.3) — it
only touches the four ingredients any institution provides (signature,
formulae, models, satisfaction), so these constructs work over any logic
Casl might be instantiated with, not just its own. Constructs covered:

- **Named specifications** — give a specification text a reusable name.
- **Extension** (`then`, §4.4.1) — add new symbols/axioms to a spec.
- **Union** (`and`, §4.4.2) — combine two specs; symbols declared in both
  are *identified*, not duplicated ("same name, same thing" — the union
  of signatures is an ordinary set union, not a disjoint one).
- **Renaming** (`with`, §4.4.3) — consistently rename symbols; not
  required to be injective, so renaming can also *collapse* distinct
  symbols together (a documented source of accidental inconsistency).
- **Libraries** (`library`/`from ... get`, §4.4.4) — named collections of
  specifications with linear visibility between them; Casl ships a
  standard library of basic datatypes.
- **Parameterisation & instantiation** (§4.4.5) — generic specifications
  (`spec SN[FP] = SP`) reusable across different actual parameters,
  instantiated via a signature-matching proof obligation
  (`Mod(AP) ⊆ Mod(FP)` up to renaming); the `given` construct handles
  symbols legitimately shared between actual parameter and body.
- **Hiding** (`hide`, §4.4.6) — the *only* structuring operator that
  increases Casl's expressive power (Bergstra & Tucker: some data types,
  e.g. naturals with a hidden squaring helper, provably have no
  hiding-free specification in equational logic with initial semantics).

`main.py`'s `Signature` dataclass plus `extension()`/`union()`/`rename()`
implement exactly the *signature-level* semantics of §4.4.1-4.4.3 (full
axiom/model-class semantics would need a theorem prover, out of scope
here). The demo reproduces Example 46 (union of two relations sharing
sort `Elem` — the merged signature has `Elem` exactly once) and Example 47
(renaming a `List` signature onto a `Monoid` signature's shape). *Not
implemented*: libraries, parameterisation/instantiation, and hiding (the
latter would need an actual model-class semantics to show its
expressiveness gain, not just signatures).

## 4.5 Closing remarks

Casl semantics is a specification's model class, possibly empty
(inconsistency). Structuring operators let you build large specifications
that stay checkable in pieces. Algebraic specification and programming
genuinely *overlap* — the chapter's own claim that "the Casl specification
of a Ladder Logic program and the program itself are semantically the
same" is echoed directly by this file's `main.py`, where the transition
relation is simultaneously an executable Python function and (informally)
a Ladder Logic program in the sense of Definition 4.

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
python "Algebraic Specification in CASL/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
