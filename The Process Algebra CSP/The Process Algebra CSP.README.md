# The Process Algebra CSP

Companion notes/code for Chapter 3, "The Process Algebra CSP" (pgs.
164-261), of Roggenbach, Cerone, Schlingloff, Schneider & Shaikh, *Formal
Methods for Software Engineering* (Springer, 2022) — see the top-level
[README.md](../README.md) for the course as a whole.

`main.py` implements a small, bounded-depth CSP engine (operational
semantics + traces model + a deadlock check) applied to the chapter's own
running examples. Run it with `python "main.py"` from this folder (see
[Environment](#environment) below).

## 3.1 Introduction

CSP ("Communicating Sequential Processes") models systems as **processes**
that synchronise on **events**. The chapter's motivating story: you and a
waiter each run a "protocol" for buying coffee. If your protocols don't
fit together — you want to pay after receiving the item, the waiter wants
payment first — the interaction **deadlocks**. If the waiter goes to the
kitchen and never comes back, that's a **livelock**. If the bistro
substitutes tea for coffee when out of beans, that's **non-determinism**.
CSP gives these three phenomena precise, checkable definitions —
reproduced in `_demo_bistro_deadlock()`.

## 3.2 Learning CSP

### 3.2.1 ATM example — syntax

Built up incrementally against a running Automated Teller Machine example:

- **Prefix & recursion**: `a -> P` performs event `a` then behaves as `P`;
  a process equation `N = P` can be recursive (`N` appears in `P`) — the
  only way CSP expresses infinite behaviour. `STOP` performs no event.
- **Channels**: events can be tagged/structured as `channel.value`
  (e.g. `CardSlot.cardI`); `channel(c)` denotes the type (event set) of a
  channel, `channels(cs)` their combined events.
- **Termination & sequencing**: `SKIP` does nothing but terminate
  (signalled by the special event `tick`, written ✓); `P ; Q` behaves as
  `P` until it terminates, then continues as `Q`. The **interrupt**
  operator `P /\ Q` behaves as `P` until an event from `Q` occurs, at
  which point `Q` takes over — used for the ATM's cancel button.
- **Choice**: `P [] Q` (external choice) offers the environment the
  initial events of both `P` and `Q`; `c?x -> P(x)` reads a value over a
  channel and can depend on it; `P <| cond |> Q` is a conditional.
  `a{x} -> P(x)` (prefix choice) lets the environment pick any event `x`
  from a set.
- **Non-determinism, composition, hiding**: `P |~| Q` (internal choice)
  lets the *process* pick, unobservably. `P [|A|] Q` (general parallel)
  synchronises `P` and `Q` on events in `A`; `interleave` (`A = {}`) and
  `sync`/lock-step (`A = Σ`) are special cases. `P \ A` hides events in
  `A`, turning them into invisible internal steps.
- **Parameters, renaming, replication**: process names can carry
  parameters (e.g. `PinCheck(n)` for attempts remaining); `P[[R]]` renames
  events through a relation `R` (e.g. one currency event fanning out into
  three); replicated operators (`[]`, `|~|`, `|||`, `[|A|]`) combine a
  family of processes over an index set.

`main.py`'s `Process` AST covers most of this: `Stop`, `Skip`, `Prefix`,
`PrefixChoice`, `ExtChoice`, `IntChoice`, `Seq`, `GenParallel`, `Hide`,
`Rename`, `Rec` (for recursion, via a thunk so Python can build the
unfolding lazily). *Not implemented*: the interrupt operator and
replicated operators.

### 3.2.2 Semantics — the jet engine controller

Introduces CSP's two semantics via an Electronic Engine Controller case
study:

- **Operational semantics**: Csp processes are *states*; **firing rules**
  define labelled transitions between them (`P --a--> P'`), with `tau`
  (τ) for silent/internal steps. The transition system reachable from a
  process is its automaton.
- **Denotational semantics**: assigns each process the *set of all
  possible observations* it can make — for the traces model, its
  possible finite event sequences, defined by structural induction over
  the syntax (one semantic clause per operator).
- Recursive process equations raise three standard questions: does a
  solution exist, is it unique, how do you construct it? (Answered via
  fixed points in Sec. 3.4.3.)

`main.py`'s `transitions()` function *is* an operational semantics for the
AST above (one dispatch arm per firing rule); `traces()` is a
bounded-depth denotational traces model built on top of it.

### 3.2.3 Refinement — buffers

A **buffer** is defined by three properties: (1) output is a *prefix* of
input, in the same order (a **safety** property, expressible with
traces); (2) an *empty* buffer must accept any input, and (3) a
*non-empty* buffer must offer some output (both **liveness**, needing
more than traces — a process can *have* a trace without *having to*
perform it).

- **Refusal sets**: a set of events a (stable) process can decline
  forever. A **failure** is a pair `(trace, refusal-set)`.
- **Refinement**: `P ⊑_T Q` ("Q trace-refines P") iff every trace of `Q`
  is a trace of `P` — Q has *fewer* behaviours, so it can only be safer.
  `P ⊑_F Q` (failures-refinement) additionally requires Q's refusals
  after any shared trace to be among P's — this is what lets a
  specification's *liveness* properties transfer to an implementation.
  `STOP` is the ⊑_T-most-refined process ("doing nothing is always
  safe"); refinement is compositional (preserved by every CSP operator).
- **Fixed-point induction** is the standard proof technique for showing
  one recursively-defined process refines another (used to prove a
  concrete two-element buffer refines the generic `BUFF`).
- A worked **communication system** example (sender/lossy-medium/receiver)
  shows a first design failing the buffer refinement (FDR finds a
  corrupting trace) and a "best-of-three" redesign passing it.

`main.py`'s `buff()` reproduces `BUFF` from Example 38.4 exactly
(non-empty buffers use internal choice to *optionally* refuse more
input, but always offer to write); `two_place_buffer()` is a concrete
bounded buffer; `_demo_buffer()` checks the prefix property empirically
over generated traces and checks `two_place_buffer ⊑_T BUFF` via
`trace_refines()`.

## 3.3 The Children's Puzzle, or what CSP tools can do

Children in a circle repeatedly (1) each pass half their candies left,
then (2) the teacher tops up anyone left holding an odd number.

- **3.3.1 Arithmetic**: a pure counting argument shows the maximum never
  increases, the minimum never decreases (Lemma 1), so the teacher
  eventually stops handing out candies (Corollary 1), and the number of
  children at the minimum strictly decreases each round (Lemma 2), so
  eventually *everyone* holds the same number of candies (Corollary 2).
  This argument implicitly assumes a global clock synchronising every
  child's steps.
- **3.3.2-3.3.3 CSP model + tools**: modelling the puzzle in CSP drops
  that synchrony assumption (each child acts independently/asynchronously)
  — showing the same stabilisation property must now be argued about a
  genuinely concurrent system. The chapter demonstrates three tiers of
  CSP tooling on this model: a **simulator** (ProBe) explores one run; a
  **model checker** (FDR) automatically checks *all* runs of one fixed
  instance (stability, deadlock-freedom, livelock-freedom, determinism);
  an **interactive theorem prover** (CSP-Prover) proves the property for
  *all* sizes and initial distributions at once — at the cost of a
  human-authored proof script (here, several thousand lines, ~1 month of
  work).
- **3.3.4 Transformation**: tools like CSP++ translate (a sublanguage of)
  CSP directly into C++, raising open questions about which processes are
  even implementable (a genuinely non-deterministic process can't be, on
  a deterministic machine) and whether the translation preserves
  properties like deadlock-freedom.

`main.py`'s `_demo_childrens_puzzle()` reproduces the arithmetic model
(Sec. 3.3.1) exactly against the book's own Berta/Emma/Hugo numbers, then
runs 20 random instances to spot-check Corollary 2. *Not implemented*: the
asynchronous CSP encoding itself (Sec. 3.3.2) — a natural extension using
this file's `GenParallel`/`Rec` machinery with per-child parametrised
recursion.

## 3.4 Semantics and analysis

### 3.4.1 The three standard models

Denotationally, CSP has (at least) three standard semantic domains, each
a **partial order** under refinement, trading off precision against
tractability:

- **Traces (`T`)**: finite event sequences a process can perform;
  prefix-closed. Cheapest to check, but can only express safety.
- **Failures/divergences (`N`)**: pairs `(trace, refusal-set)` plus the
  set of traces after which the process can *diverge* (livelock — loop
  forever on invisible events). Most expressive of the three, but the
  denotational clause for hiding is only defined for finitely-branching
  processes, and its fixed-point theory misbehaves over infinite
  alphabets.
- **Stable failures (`F`)**: like `N` but *ignoring* divergence — simpler
  clauses (hiding becomes easy), agrees with `N` exactly on
  divergence-free processes (Theorem 7), but can't itself express
  divergence-freedom.
- Trace-refinement does **not** imply failures-refinement (Example 41,
  Corollary 3): `STOP` trivially trace-refines any "safe" process — safety
  alone can't rule out "does nothing," which is exactly why liveness
  needs a richer model.

### 3.4.2 Algebraic laws

CSP processes obey algebraic laws (idempotence/symmetry/associativity of
choice, distributivity over internal choice, "step laws" giving a
compound process's initial events from its parts' initials) — some hold
in every standard model, others only in specific ones (e.g. `P [] Q =_T
P |~| Q`: traces can't distinguish external from internal choice, but
failures can). These laws are what tools like CSP-Prover mechanise to
prove process equalities/refinements by rewriting instead of by
unfolding semantics by hand.

### 3.4.3 Foundations: fixed points

Recursive equations `P = f(P)` are given meaning as **fixed points** of
`f` over a domain ordered by refinement. Key results, illustrated on
`P = a -> P`:

- The traces domain ordered by `⊆`, with `{<>}` as bottom, is an
  **ω-complete partial order** (every ω-chain has a least upper bound).
- **Kleene's fixed point theorem**: a continuous function on a pointed
  cpo has a *least* fixed point, constructed as `lub{fⁿ(⊥) : n ∈ ℕ}` —
  for `a -> P` this is exactly the set `{aⁿ : n ∈ ℕ}`, i.e. `P`'s
  intuitive meaning ("any number of `a`s"). Taking the *smallest* fixed
  point is what makes the recursive equation's solution unique.
- This answers the three questions raised in 3.2.2 (existence, uniqueness,
  construction) for `T` and `N` in general, and for `F` when the alphabet
  is finite.

### 3.4.4 Checking for general global properties

The chapter's recurring "trick": encode a property as a CSP process
`Prop`, then show *any* refinement of `Prop` inherits the property.

- **Livelock-freedom**: `P` is livelock-free iff `P ⊑_N DivF` fails for
  no reason other than... actually iff `divergences(P) = {}`. `DivF`
  (the most general livelock-free process) is the ⊑_N-maximal livelock-
  free process, so `P` is livelock-free **iff** `P ⊑_N DivF`
  (Corollary 6) — refinement of `DivF` is a sound *and complete* proof
  method for livelock-freedom.
- **Deadlock-freedom**: analogously, `DF` (able to perform every event
  from every state) is the ⊑_F-maximal deadlock-free process, and `P` is
  deadlock-free **iff** `P ⊑_F DF` (Corollary 7).
- **Determinism**: `P` is deterministic iff no reachable trace `s` and
  event `a` have both `s⌢<a>` a valid trace *and* `{a}` a valid refusal
  after `s`. Checked via a clever refinement encoding (Lazić/Roscoe): run
  two renamed copies of `P` connected through a `Monitor` process; `P` is
  deterministic iff the result refines a process `Det` that can never
  deadlock after an odd-length trace (Theorem 18).

`main.py`'s `deadlock_free()` is a direct, bounded-depth analogue of
Corollary 7's idea (search for *any* reachable stable state with zero
outgoing transitions) rather than a refinement check against `DF` — the
same property, checked more directly since this toolkit has no failures
model to refine against. *Not implemented*: livelock-freedom and
determinism checks, and the failures/divergences model they properly
rely on.

## 3.5 Closing remarks

No single CSP semantic model is "best" — each patches a shortcoming of a
coarser one at a real cost (traces are cheap but safety-only; failures/
divergences add liveness and livelock but break hiding's semantics over
infinite alphabets; stable failures fixes that by giving up on
divergence-tracking). The chapter compares this directly to classical vs.
quantum mechanics: pick the simplest model that still answers the
question you actually have.

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
python "The Process Algebra CSP/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
