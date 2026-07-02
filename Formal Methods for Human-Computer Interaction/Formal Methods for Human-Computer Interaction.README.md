# Formal Methods for Human-Computer Interaction

Companion notes/code for Chapter 7, "Formal Methods for Human-Computer
Interaction", of Roggenbach, Cerone, Schlingloff, Schneider & Shaikh,
*Formal Methods for Software Engineering* (Springer, 2022) — see the
top-level [README.md](../README.md) for the course as a whole.

**A sourcing note:** the book models human cognition with a CSP extension
implemented in PAT (integer variables, arrays, guarded events); nearly all
of the actual PAT source listings (Examples 65.3 through 65.19) are
formatted code blocks/images that did not survive plain-text extraction —
only the surrounding prose explanations did. So `main.py` is an original
Python re-formalization of the *mathematical* model the chapter gives in
prose (particularly Sec. 7.3.3's precise enabling/performance/closure
conditions for a "basic activity"), not a transcription of the book's PAT
code. It reproduces the chapter's central example — the ATM
post-completion error — mechanically, from first principles, rather than
by copying a listing.

Run `python "main.py"` from this folder (see [Environment](#environment)
below).

## 7.1 Human errors and cognition

Opens with a cognitive-error story (a cake burns despite a "tested"
temperature trick) to make the chapter's central design point: **you
cannot expect human behaviour to adapt to an algorithm — the algorithm
must be designed around actual human cognitive performance.** The chapter
unifies two previously-separate research threads under one formal
framework:

- **User**: performs everyday activities (baking, driving, using an ATM)
  mostly under *automatic* control, triggered by a goal and then largely
  running itself.
- **Operator**: performs deliberate, attention-heavy monitoring tasks
  (air traffic control, plant control rooms) driven by a *purpose* rather
  than a single terminal goal — failing to hit any one goal isn't
  necessarily a task failure, as long as the purpose is still being served.

## 7.2 Human memory and memory processes

Three memory stores: **sensory** (perception persists briefly),
**short-term/working memory (STM)** (small capacity, fast access, fast
decay), and **long-term memory (LTM)** (effectively unlimited, slow
access, little decay, and internally split into **declarative** —
episodic + semantic, "knowing what" — and **procedural** — "knowing how,"
built up from declarative memory through repetition).

- **STM & closure**: Miller's classic result — STM holds about 7±2
  *chunks* (not raw items) — and **closure**: once a task completes, the
  information used for it is subconsciously purged from STM, freeing
  capacity. This single mechanism is the chapter's main source of
  emergent errors.
- The chapter first sketches a "pure CSP" STM model (`n` numbered
  states, `store`/`remove`/`closure`/`delay` actions) then notes it
  doesn't scale, motivating PAT's array-based extension (an `stm` array +
  size counter, with `store`/`retrieve`/closure as guarded, annotated
  events) — which is what the rest of the chapter actually uses.

`main.py`'s `BasicActivity`, `is_enabled()`, and `perform()` implement
this STM+closure model directly as Python sets rather than PAT arrays —
same semantics (bounded, flush-on-goal-completion), simpler substrate.

## 7.3 Human behaviour and interaction

Formalizes a task as a hierarchy of goals decomposed into **basic
activities** — units that need no further decomposition. A basic activity
under automatic control is a quadruple `(perception, retrieve, store,
action)`: it fires when the named perception is available, the `retrieve`
items are present in STM, and the `store` items aren't already there;
performing it removes `retrieve`, adds `store`, executes `action` — and,
if the action **achieves an active goal**, triggers closure (flush
everything but unachieved goals).

- **7.3.3 Automatic control**: driven by perceptions + STM contents, not
  goals directly — reactive but not purely so (implicit attention still
  moves perceptions into STM). This is where classic cognitive errors
  live (Sec. 7.5.1's central case study).
- **7.3.4 Deliberate control**: adds a **goal** as an explicit fifth
  component — the activity is also gated on a specific goal being active,
  and the goal *drives* the task (e.g. sub-goaling: "the box is heavy" →
  establish the sub-goal "empty it first").
- **7.3.5-7.3.6**: an operator's behaviour is mostly deliberate, driven by
  *purpose* rather than a terminal goal; familiar perceptions let control
  switch from deliberate back to automatic (an ATM user goes "on
  autopilot" once the interaction feels routine), and unexpected
  perceptions (decisions, danger) switch it back.

## 7.4 Interface/system model — the ATM case study

A user's *perception* is identified with the interface's corresponding
*output* — e.g. "cash delivered" is both an interface state and the
perception that triggers the user's next automatic activity. The
chapter's running case study: an **old ATM** design delivers cash *before*
returning the card; a **new ATM** design returns the card *first*. Both
are functionally identical from a pure task-completion standpoint — the
book's point is that the *ordering* alone determines whether a real,
well-documented HCI bug (the **post-completion error** — forgetting the
card once the "real" goal, cash, is in hand) can even arise, purely as a
side effect of the closure mechanism from Sec. 7.2.1. Section 7.4.1
extends this with **experiential knowledge/expectations** and a
**Supervisory Attentional System** (Norman & Shallice) that can switch a
user from automatic to deliberate control when a perception is assessed
as dangerous, novel, or otherwise demanding — e.g. a user experienced
with the *old* ATM, confronted with a *new* one, may misread the early
card return as a danger signal and abandon the session.

`main.py`'s `simulate()` runs exactly this case study: two ATM
interfaces (`OLD_INTERFACE`, `NEW_INTERFACE`) that differ only in whether
cash or card comes first, both built from the *same* four
`BasicActivity` rules. Running it reproduces the bug mechanically: in the
old interface, collecting the cash achieves the goal and triggers
closure, which flushes the `collectCard` reminder from STM *before* the
card-return perception ever arrives — so the user's automatic-control
model has no rule left to react to it, and the simulation gets stuck
exactly where a real user would forget the card. The new interface
collects the card first (consuming the reminder while it's still in STM),
so no such gap ever opens. *Not implemented*: the experiential-
knowledge/SAS extension (Sec. 7.4.1) — the `SystemNewUserOld` edge case
the book itself flags as its most interesting verification result.

## 7.5 Model checking analyses

Three kinds of properties, checked with PAT's LTL model checking
(`#assert system |= property`):

- **Functional correctness**: the user/operator can always complete the
  task (accomplish the goal).
- **Non-functional correctness**: the goal is reached, but some other
  property is violated (e.g. the card is forgotten) — this is exactly
  where the ATM case study's bug shows up formally.
- **Cognitive overload**: STM exceeds a defined capacity limit.

The book's own property schemas: functional correctness as `[](choose ->
(!begin U accomplish))`, and a safety schema `[](internal -> (!begin U
return))` for "once some internal event happens, the environment doesn't
start a new session before returning some held resource." Running these
against the ATM models via PAT, the book reports the safety property
holding for both `SystemNewUserNew` and `SystemNewUserOld` (new ATM) and
failing for both old-ATM variants, independent of user experience — and,
separately, **Example 69.2** finally answers the chapter's opening cake
mystery: the "raise-then-lower the temperature" algorithm splits into two
sub-tasks with a goal-completion (closure) point in between, so the
"lower the temperature" step — stored as a reference-to-the-future *before*
that closure point — gets silently flushed, exactly like the ATM's
forgotten card. (The chapter also cites a real aircraft incident with the
same root cause: engine cowl doors left unlatched after maintenance.)

`main.py`'s `_demo_ltl_verification()` checks a simplified version of
both schemas against the simulated ATM traces and reproduces the book's
core claim exactly: functional correctness holds for both interfaces
(both eventually collect the cash), but the safety property holds only
for the new interface — the old one fails it precisely because of the
closure bug demonstrated above.

**7.5.2 Task-failure analysis** applies the same LTL machinery the other
direction: given an empirically-derived decomposition of a task failure
`F` into behaviour patterns `P₁, ..., Pₙ`, check it's **sound** (each `Pᵢ`
⟹ `F`) and **complete** (`F` ⟹ `P₁ ∨ ... ∨ Pₙ`) — i.e. verify a piece of
applied psychology's own causal model against a formal one. Example 66.3
reports exactly this outcome for a real air-traffic-control failure
decomposition: sound, but *not* complete — PAT's counterexample revealed
a genuine failure mode the empirical decomposition had missed (a
"contrary decision process" pattern folded incorrectly into another
category), leading the authors to refine the decomposition.

`main.py`'s `_demo_soundness_completeness()` is an original, small
illustration of this exact methodology (not a transcription of the ATC
scenario, which is described only qualitatively in the source): a
2-pattern decomposition that is sound but demonstrably incomplete, with
the counterexample trace printed directly — mirroring Example 66.3's
own sound-but-incomplete finding.

## 7.6-7.7 Closing remarks and research directions

The chapter's honest self-assessment: this framework presupposes
expectations are fixed a priori (not the product of ongoing learning),
that cognition is context-independent, and that actions are triggered by
isolated perceptions — all simplifications. Current research (as of the
book's writing) points toward richer modelling substrates (Maude, the
authors' own Behavioural and Reasoning Description Language) for
multi-agent, learning, and multimodal extensions, and toward grounding
models in real interaction-log data rather than a priori assumptions
alone.

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
python "Formal Methods for Human-Computer Interaction/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
