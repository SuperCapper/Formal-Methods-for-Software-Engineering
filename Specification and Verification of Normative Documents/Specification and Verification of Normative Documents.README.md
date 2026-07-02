# Specification and Verification of Normative Documents

Companion notes/code for Chapter 6, "Specification and Verification of
Normative Documents", of Roggenbach, Cerone, Schlingloff, Schneider &
Shaikh, *Formal Methods for Software Engineering* (Springer, 2022) — see
the top-level [README.md](../README.md) for the course as a whole.

**A sourcing caveat, upfront:** this chapter leans unusually heavily on
symbolic formulas — the contract language `CL`'s syntax/semantics live in
Figs. 6.2-6.6, and Examples 55, 56, 56.1, 58-63 all hinge on specific `CL`
expressions. Those figures and inline formulas are typeset as images/
MathML in the source EPUB and did not survive plain-text extraction —
only the surrounding prose did. So `main.py` is *not* a transcription of
the book's exact trace-semantics rules; it's an original formalization
grounded in what the prose clearly establishes (the syntax description in
Sec. 6.4.1, the walk-through of how a residual contract evolves in Sec.
6.4.2.1, and Definition 1's conflict criteria, stated in prose in Sec.
6.5.1.1). Where the book's own worked examples can't be checked against
this file (their formulas are the missing images), the demo instead
reproduces Example 57's point — which *is* fully recoverable in prose —
about the airport ground-crew contract.

Run `python "main.py"` from this folder (see
[Environment](#environment) below).

## 6.1-6.2 Contracts: what and why

Motivates the chapter with two real-world horror stories (a surprise
roaming bill, an unread cancellation-fee clause) to argue that "contract"
in computer science covers far more than pre/post-conditions — it means
any document of **obligations, permissions, and prohibitions**: legal
agreements, terms of service, and *workflow specifications* (e.g. an
airline ground crew's procedures, Example 53) are all "contracts" in this
sense. The chapter's own recurring examples:

- **Example 53** (ground crew): 10 numbered clauses of obligations and
  prohibitions around opening/closing a check-in desk, issuing boarding
  passes, and a general fine-on-violation clause.
- **Example 54** (ISP contract): obligations/rights of an internet
  provider and client, including conditional payment clauses and
  termination conditions.

## 6.3 A framework for specification and analysis of contracts

A pipeline (Fig. 6.1): natural language → **Controlled Natural Language**
(CNL, a restricted, machine-parseable English) → the formal language `CL`
(the "eCon") → a **Contract Analyser** (checks for conflicts and
user-defined properties, producing counter-examples) → an approved
contract, from which a **runtime monitor** can be generated to watch a
live system and flag violations, feeding a log back to a **Violation
Analyser** for offline liability analysis. Most of this pipeline is
manual/semi-automated in practice (Sec. 6.5.2's own case studies confirm
this) — the chapter presents it as a long-term research vision, with the
rest of the chapter covering the pieces that *are* realized.

## 6.4 The language `CL`

An action-based language (modalities apply to *actions*, not
states-of-affairs), influenced by dynamic, temporal, and deontic logic
(Chapter 2, Sec. 2.5):

- **Actions**: basic named actions combined via concurrency (`&`),
  sequence (`.`), choice (`+`), and Kleene star (`*`, disallowed inside
  deontic operators); `0` (impossible action) and `1` (skip/matches
  anything).
- **Contracts**: `O(α, C)` — obligation to perform `α`, with reparation
  `C` (a Contrary-to-Duty clause) if not fulfilled; `F(α, C)` — prohibition
  of `α`, with reparation `C` (Contrary-to-Prohibition) if violated;
  `P(α)` — permission (no reparation possible — permissions can't be
  violated); conjunction of clauses; `[α]C` — a dynamic-logic-style
  condition, `C` only applies once `α` has occurred. A designated
  mutual-exclusion relation `#` on actions (e.g. "open the desk" # "close
  the desk") lets the specifier declare which actions can't co-occur.
- **Semantics**: three variants exist — an encoding into the π-calculus
  (for expressiveness results), a Kripke semantics (fully precise, but
  complex enough that it mainly matters for a hypothetical model checker),
  and a **trace semantics** (used for both monitoring and conflict
  analysis, and the one this file's code approximates). A trace
  judgement pairs an *action* trace with a *deontic* trace recording
  which obligations/permissions/prohibitions were in force at each point
  — deliberately extended (beyond the trace semantics' original
  monitoring-only design) to carry deontic information and accept finite
  prefixes, specifically so conflict analysis has something to point at.

`main.py`'s `Contract` AST (`Fulfilled`, `Violated`, `Obligation`,
`Prohibition`, `Permission`, `And`, `Condition`) and `step()` function are
this file's own residual-contract semantics: `Obligation`s are one-shot
(the named action is due on the *very next* step, or the reparation takes
over — matching the chapter's own "after a is executed, an obligation to
do b [next] is enacted" narrative); `Prohibition`s and `Condition`s
persist across steps until triggered (a standing ban or a still-dormant
rule); `And` combines clauses, collapsing to `Violated` the moment either
side does. *Not implemented*: the actual action algebra (`&`/`./+/*`
regular-expression-style compound actions) — obligations/prohibitions
here take a single concurrent-action-set, not a full action expression.

## 6.5 Verification of contracts

### 6.5.1 Conflict analysis

The chapter's main technical payload. **Definition 1** names four kinds
of normative conflict, all checked at some reachable point in a
contract's execution:

1. the same action is simultaneously **obliged and forbidden** — any
   choice violates the contract;
2. the same action is simultaneously **permitted and forbidden** — a
   *potential* conflict (only real if the permission is exercised);
3. two mutually-exclusive actions are both **obliged** — a real conflict
   (both can't be discharged);
4. one of two mutually-exclusive actions is **obliged**, the other
   **permitted** — potential, symmetric to case 2.

(Two mutually-exclusive actions both *permitted* is explicitly **not**
flagged — the chapter calls this a "philosophical question" left open.)

**Example 57** is the chapter's cautionary tale: two individually
sensible ground-crew clauses ("obliged to open the desk two hours before
the flight" / "obliged to close it 20 minutes before") look
conflict-free to any human, because the human tracks *when* each applies.
A naive formalization that drops the timing and declares both as
unconditional obligations on mutually-exclusive actions (open/close)
produces exactly conflict case 3 — a **spurious** conflict, an artifact
of over-abstraction, not a real flaw in the contract. The chapter's
implicit fix: encode the missing ordering with `CL`'s `[α]C` condition, so
the obligation to close only becomes active once open has already
happened.

The book's own machinery for finding conflicts algorithmically —
Definitions 2-3, the residual function `f` (Fig. 6.4), the automaton
construction function `κ` (Figs. 6.5-6.6), and the correctness/
completeness results (Lemma 1, Proposition 1, Lemma 2, Theorem 1) —
build a finite-state automaton from a contract and run reachability
analysis over it, exactly mirroring how a model checker looks for a bad
state. That automaton-construction machinery is what got lost to
extraction here; `main.py`'s `find_conflict()` instead does the same
*kind* of thing directly by bounded reachability search over `step()`,
which is enough to demonstrate the idea (and to catch Example 57's
spurious conflict) without literally implementing Figs. 6.4-6.6.

### 6.5.1.5 CLAN, and 6.5.2 `LKit`

**CLAN** is the prototype conflict analyser tool implementing the above.
`LKit` wraps it in a full pipeline: a hand-written **Controlled Natural
Language** (restricted English, e.g. `{ground crew} must {open the check-
in desk}`) is parsed via the **Grammatical Framework** (GF — a
bidirectional grammar formalism with a shared abstract syntax, so the
same tool can linearise counter-examples back into readable CNL, not just
parse forward) into `CL`, checked by CLAN, and any counter-example is
translated back into CNL for a human to locate in the original document.
Case studies on Examples 53 and 54 found real conflicts only after
several iterations of fixing *modelling* bugs (like Example 57's) first —
underscoring that most early "conflicts" found in practice are artifacts
of the formalization, not the original document.

### 6.5.3-6.5.4 Runtime verification and model checking

Both are sketched only briefly. A conflict-analysis automaton *can*
sometimes double as a runtime monitor, but generally can't — a real
monitor needs to bind to concrete system events (not abstract action
names) and handle actual computation (averages, percentages), which the
automaton has no notion of. Model checking `CL` contracts has no
dedicated tool; the chapter's own applied path went `CL` → π-calculus
variant → Kripke-style LTS → NuSMV input, iterating on counter-examples.

## 6.6 Closing remarks

`CL` is offered as a candidate formal core for the "eCon" stage of Fig.
6.1's pipeline, with conflict analysis as its most mature analysis. The
chapter is honest that most of the pipeline — NL-to-CNL translation,
runtime monitor extraction for anything beyond simple contracts, and a
richer property/query language — remains open research, not solved
tooling.

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
python "Specification and Verification of Normative Documents/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
