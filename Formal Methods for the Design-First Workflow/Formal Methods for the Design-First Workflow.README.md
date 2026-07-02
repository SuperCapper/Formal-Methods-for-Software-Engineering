# Formal Methods for the Design-First Workflow

**This folder is different from the others in this repo.** Chapters 1–8
each have companion notes and code extracted and reconstructed from
Roggenbach, Cerone, Schlingloff, Schneider & Shaikh's *Formal Methods for
Software Engineering*. This folder is not from the book — it's an
original synthesis showing how the techniques from those eight chapters
compose into practical tooling for a **Design-First development
workflow** (design.md → requirements.md → tasks.md → implementation),
for both conventional software engineering and AI/agentic-system
engineering.

`main.py` implements three small tools and runs them against two worked
examples — a notification-system architecture and a multi-agent
tool-calling architecture — showing each tool catching a real class of
bug before it reaches implementation. Run it with `python "main.py"`
from this folder (see [Environment](#environment) below).

## Why formalize a Design-First workflow at all

The workflow's own stated benefit is that "requirements are guaranteed
to be technically feasible since they're derived from a validated
architecture" — but *validated* is doing a lot of work in that sentence.
An architecture reviewed only by eye can still contain a circular
dependency; a set of requirements that each individually look reasonable
can still contradict each other once you consider what triggers them
together. Both of those are exactly the kind of defect Formal Methods
exist to catch mechanically rather than by inspection — and both recur,
almost unchanged, across several chapters of the book this repo is built
from.

## What each chapter contributes to which stage

| Stage | Chapter(s) | What transfers |
|---|---|---|
| **Design phase** (architecture, component interactions) | [Ch. 3 — CSP](../The%20Process%20Algebra%20CSP/) | Deadlock analysis (Sec. 3.4.4): a synchronous-call "waits-for" graph has exactly the structure of CSP's synchronisation, and a cycle in it is a deadlock regardless of what each component actually does. `main.py`'s `find_deadlock_cycle()` is this idea applied directly to an architecture diagram. |
| **Design phase** (data model, API contracts) | [Ch. 4 — CASL](../Algebraic%20Specification%20in%20CASL/) | Signatures + axioms for specifying an API or data model precisely (sorts/ops/preds), plus consistency checking (is the spec even satisfiable?) before a single line of implementation exists. |
| **Design phase** (security-sensitive components) | [Ch. 8 — Security Protocols](../Formal%20Verification%20of%20Security%20Protocols/) | The Dolev-Yao intruder model and message-derivation analysis apply directly to any design involving auth tokens, API keys, or inter-service credentials — including AI systems calling third-party tool APIs with delegated credentials. |
| **Requirements phase** (acceptance criteria) | [Ch. 2 — Logics](../Logics%20for%20Software%20Engineering/), [Ch. 5 — Testing](../Specification-Based%20Testing/) | LTL as the target language for "WHEN X the system SHALL eventually Y"-style EARS requirements (Ch. 2), and Ch. 5's exact technique (Algorithm 7, Sec. 5.2.3) for checking such a formula against an execution trace as a test oracle. `main.py`'s `to_ltl()`/`check()` are this pipeline end to end. |
| **Requirements phase** (conflict detection) | [Ch. 6 — Normative Documents](../Specification%20and%20Verification%20of%20Normative%20Documents/) | Definition 1's four kinds of normative conflict (same trigger, contradictory obligations; obligation + prohibition on the same action) map directly onto contradictory SHALL/SHALL-NOT requirements sharing a trigger. `main.py`'s `find_conflicts()` is a direct port. Example 57's warning — that abstracting away context turns a real non-conflict into an apparent one, or vice versa — is precisely why *interaction effects* between individually-reasonable requirements need a checker, not just a reviewer. |
| **Requirements phase** (human-facing behaviour) | [Ch. 7 — HCI](../Formal%20Methods%20for%20Human-Computer%20Interaction/) | For any requirement involving a human in the loop (approval prompts, confirmation dialogs, alerts), the closure/post-completion-error mechanism is a concrete, checkable failure mode: does completing goal A cause the system to "forget" a still-pending obligation B? Directly relevant to agentic systems with human-approval gates. |
| **All stages** (what makes any of this rigorous) | [Ch. 1 — Formal Methods](../Formal%20Methods/) | Definition 1 (syntax + semantics + method) is the standard this whole table is implicitly holding each artefact to: a design.md or requirements.md is only as checkable as it is *precise* — which is exactly the gap between an EARS requirement and an ordinary user story. |

## What's implemented here

### 1. EARS requirements → LTL (`parse_ears`, `to_ltl`, `check`)

Parses the five standard EARS patterns (ubiquitous, event-driven,
state-driven, unwanted-behaviour, optional-feature, plus the combined
state+event form) via regex into a `Requirement`, and translates each
into an LTL formula using the same `Prop`/`Not`/`Implies`/`Always`/
`Eventually` toolkit built in Chapters 2 and 5. This isn't a universal
translation — the README is explicit that whether a "WHEN" requirement
means *eventually* or *immediately next* is a judgement call the
requirement's author needs to make explicit — but it's enough to take an
EARS requirement all the way to a pass/fail check against a concrete
execution trace, exactly Chapter 5's Algorithm 7 test-oracle technique.

### 2. Requirement conflict detection (`find_conflicts`)

Flags pairs of requirements sharing a trigger/state/condition whose
responses directly contradict — either an explicit SHALL vs. SHALL NOT
on the same response, or two responses the spec author has declared
mutually exclusive (mirroring Chapter 6's own mechanism: the specifier
must state which actions are mutually exclusive, since the tool can't
infer that "skip confirmation" and "request confirmation" are opposites
from the text alone).

### 3. Architecture deadlock checking (`Architecture`, `find_deadlock_cycle`)

Models an architecture as a directed "waits-for" graph (which components
block synchronously on which others) and runs cycle detection — the same
structural condition that makes a CSP synchronous parallel composition
deadlock, generalised from process algebra to service architecture
diagrams.

## The two worked examples

- **Software engineering** (`_demo_notification_system`): the WebSocket
  notification architecture from the workflow's own "High Level Design"
  example prompt. Verified: a Lambda function with an innocent-looking
  synchronous callback to an "EnrichmentService" that calls back into
  Lambda creates a real deadlock cycle the checker catches; two EARS
  requirements ("deliver messages" vs. "discard messages immediately,"
  both triggered by "a message is published") are flagged as
  contradictory; and the first requirement is checked as an LTL
  acceptance criterion against both a passing and a failing simulated
  trace.
- **AI engineering** (`_demo_multi_agent_system`): a Research/Writer
  multi-agent architecture where each agent synchronously awaits a
  response from the other (a real, easy-to-introduce bug in agentic
  system design — invisible in a sequence diagram that only shows one
  direction at a time, immediately visible once modelled as a graph).
  A second example shows a *legitimate* confirmation-on-deletion policy
  and a *legitimate* autonomous-mode policy combining to produce a
  genuine contradiction only once both apply to the same trigger —
  exactly the "each rule looks fine in isolation" failure mode Chapter
  6's ground-crew example warns about.

Both demos were run end to end while writing this file; every claim
above (which architecture deadlocks, which requirements conflict, which
traces pass or fail) reflects the tool's actual output, not a prediction.

## How to use this in your own Design-First workflow

1. **During the Design phase**, once `design.md` describes component
   interactions, encode the synchronous-call relationships as an
   `Architecture` and run `find_deadlock_cycle()` before locking in the
   architecture — this is cheap and catches a real, recurring class of
   bug (doubly so for multi-agent designs, where "who's waiting on whom"
   is easy to lose track of across several agents).
2. **During the Requirements phase**, write acceptance criteria in EARS
   form from the start (the workflow already generates "system behaviors
   in EARS format" per its own description) and run `find_conflicts()`
   over the full requirement set — not just newly-added requirements,
   since Chapter 6's lesson is that conflicts are usually *interaction*
   effects between requirements that were each written and reviewed in
   isolation.
3. **During Implementation/testing**, reuse the same EARS→LTL
   translation as a runtime or test-time oracle (`check()`), exactly
   Chapter 5's technique — the requirement you wrote during the
   Requirements phase becomes the property your tests (or your running
   system, via a lightweight event log) are checked against, rather than
   being re-interpreted from prose at test-writing time.

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
python "Formal Methods for the Design-First Workflow/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
