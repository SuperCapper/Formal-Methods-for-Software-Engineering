# Logics for Software Engineering

Companion notes/code for Chapter 2, "Logics for Software Engineering" (pgs.
85-157), of Roggenbach, Cerone, Schlingloff, Schneider & Shaikh, *Formal
Methods for Software Engineering* (Springer, 2022) — see the top-level
[README.md](../README.md) for the course as a whole.

`main.py` implements two small, runnable toolkits that mirror the chapter's
own definitions (propositional logic and multimodal/Kripke logic), applied
to the chapter's own examples. Run it with `python "main.py"` from this
folder (see [Environment](#environment) below).

## 2.1 Logic in computer science

Every logic used in computer science is a *formal method* built from three
parts: a **syntax** (a grammar for well-formed formulae), a **semantics**
(what "model", "satisfaction" and "validity" mean), and a **method**
(algorithms to decide which formulae hold in a model, or in all models).
The chapter opens with a classic three-basket TV quiz puzzle to motivate
this — reproduced in `_demo_quiz_puzzle()`.

## 2.2 Propositional logic

The archetypical modelling language, illustrated throughout with a car
*configurator* example (colours, engines, gearboxes as proposition
symbols; manufacturer constraints as formulae; a customer's wishlist is
satisfiable iff it doesn't conflict with those constraints).

- **Syntax** (Def. 1): formulae are built from proposition symbols, `false`,
  and `->`, with `~`, `&`, `|`, `<->` as derived abbreviations.
- **Semantics** (Def. 2): a *model* is a truth assignment to every
  proposition symbol; the validation relation `M |= f` is defined
  structurally over `f`.
- **Satisfiability / validity** (Def. 3): `f` is satisfiable if some model
  validates it; valid (a tautology) if *every* model does. `f` is valid iff
  `~f` is unsatisfiable — so a single SAT procedure answers both questions.
- **Methods** (2.2.3): model checking is linear in formula size; SAT is
  the canonical NP-complete problem (solved here by brute-force
  enumeration over `2^n` models — real solvers like MiniSAT/Chaff use
  DPLL/CDCL instead); proof systems (Hilbert-style axioms + modus ponens,
  Gentzen natural deduction, resolution) let you *derive* validity by hand.
  Hilbert-style correctness (derivable ⟹ valid) and completeness (valid ⟹
  derivable) together give `⊢ f  iff  ⊨ f`.

`main.py` provides: a `Formula` AST (`Var`, `Not`, `And`, `Or`, `Implies`,
`Iff`, `Const`), `evaluate` (model checking), `all_models`/`is_satisfiable`/
`is_valid`/`find_model`/`entails` (Def. 2-3), `truth_table`, and a
recursive-descent `parse()` for strings like `"p & (q -> ~r)"`.

## 2.3 A framework for logics (institutions)

Generalizes the pattern above: a logic is a *signature* (symbol set) + a
set of *formulae* over it + a class of *models* + a *satisfaction relation*.
This is Goguen & Burstall's notion of an **institution**. Key ideas:

- **Model morphisms**: for propositional logic, `M ⇒ M'` if every symbol
  true in `M` is also true in `M'` — a partial order on models.
- **Loose vs. initial vs. final semantics**: a specification's meaning can
  be *all* satisfying models (loose, used by Casl), the *smallest* one
  w.r.t. `⇒` (initial — minimal feature set), or the *largest* (final —
  maximal feature set).
- **Signature morphisms & reducts**: renaming/translating symbols between
  signatures induces a translation on formulae and a "reduct" operation on
  models, satisfying the **satisfaction condition**
  `M' |=_Σ' translate(σ, f)  iff  reduct(σ, M') |=_Σ f` — i.e. "truth is
  invariant under change of notation." This is what makes *modular*
  specification (combining sub-specifications with different signatures,
  as in Casl — Chapter 4) mathematically sound.

## 2.4 First- and second-order logic

- **FOL** (2.4.1): extends propositional logic with a signature of
  function/relation symbols + individual variables, terms, and
  quantifiers `∀x`, `∃x` (Def. 8-14). Worked example: a strict partial
  order (`asymmetric ∧ transitive`) used to check feasibility of a project
  schedule. Correctness/completeness carries over from propositional logic
  via a Hilbert-style calculus extended with exemplification/
  particularization rules (or, dually, instantiation/generalization).
- **Second-order logic** (2.4.2): FOL cannot pin down equality, finiteness
  of the universe, or induction with a *finite* axiom set. Quantifying over
  predicates (not just individuals) fixes this — e.g. Leibniz's
  extensionality principle, Dedekind finiteness, and monadic
  second-order (MSO) formulations of induction and reflexive-transitive
  closure all require `∃P`/`∀P`.
- **Casl's logic** (2.4.3): many-sorted FOL with equality, **partial**
  functions (with a `def` predicate for definedness), and **sort
  generation constraints** (`generated`/`free` types) — Casl's practical
  syntax for the second-order term-generatedness properties above.

*(Not implemented in code here — FOL model checking needs a first-order
structure + quantifier evaluation over a domain, which is a natural
follow-on exercise on top of the propositional `evaluate()`.)*

## 2.5 Non-classical logics

Classical logic is "static": it can't naturally express alternatives,
subjective viewpoints, time, space, or resource consumption. Three
non-classical logics address some of these:

- **(Multi)modal logic** (2.5.1): adds `◇` ("possibly")/`□`
  ("necessarily"), interpreted over **Kripke models** — a set of possible
  worlds plus an accessibility relation per modality (Def. 27-28).
  `M, w |= □_R f` iff `f` holds at every `R`-successor of `w`; `◇_R f` is
  the dual. Multimodal logic embeds into the two-variable fragment of FOL.
  `main.py`'s `KripkeModel`/`Box`/`Diamond`/`eval_modal` implement this,
  demoed on the chapter's small "web page" graph example.
- **Deontic logic** (2.5.2): reuses modal syntax for **obligation** `O` and
  **permission** `P` (`Pf := ¬O¬f`) instead of necessity/possibility.
  Motivating examples: airport ground-crew obligations, and "John's
  party" — which also demonstrates **Chisholm's paradox**: naive Standard
  Deontic Logic (SDL) can derive both `O(tell)` and `O(¬tell)` from a
  seemingly consistent set of conditional obligations, showing classical
  modal axioms (like `Op → p`) don't transfer cleanly to norms.
- **Temporal logic / LTL** (2.5.3): `□`/`◇` reinterpreted over the flow of
  time (formulae evaluated on infinite sequences of propositional models),
  plus `X` (next) and the more expressive binary `U` (until): `f U g`
  means `g` eventually holds and `f` holds at every point until then.
  `◇f := true U f`. Motivating example: Dijkstra's **dining philosophers**
  — e.g. "philosopher 0 will always eventually eat" is
  `□◇eating_0` (infinitely-often liveness), checked in practice with tools
  like PAT (CSP + LTL model checking).

*(Not implemented in code here — LTL semantics need infinite/lazy traces;
a finite-trace/bounded LTL checker over a fixed-length sequence of
propositional models would be a natural extension of `evaluate()`.)*

## 2.6 Closing remarks

No single logic suffices for all of software engineering: logics trade off
**expressiveness** against **decidability/complexity**, target different
**application domains** (static structure vs. norms vs. time), and differ
in available **tool support** (SAT/SMT solvers, theorem provers, model
checkers). Choosing the right logic for a given specification task is the
practical skill this chapter builds toward.

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
python "Logics for Software Engineering/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
