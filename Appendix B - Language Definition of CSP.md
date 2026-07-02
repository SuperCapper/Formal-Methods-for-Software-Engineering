# Appendix B — Language Definition of CSP

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

## B.1 Syntax

### B.1.1 Processes

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

### B.1.2 Operator Precedence

Recovered verbatim from the source (this determines how many brackets a
CSP expression needs): from tightest- to loosest-binding —

1. renaming
2. prefix, guard, and sequential composition
3. interrupt, external choice, internal choice
4. the parallel operators
5. conditional

### B.1.3 Process Equations

A process equation has the form `N = P`, where `N` is a process name and
`P` is a process term as given by the grammar above (Sec. B.1.1). See
Chapter 3, Sec. 3.4.3 for how recursive process equations are given
semantics via fixed points.

## B.2 Semantics

### B.2.1 Static Semantics

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

### B.2.2 Syntactic Sugar

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

### B.2.3 Core Language

The appendix isolates a minimal core language from which the rest is
derived (the specific figure delineating "core" vs. "derived" operators
did not survive extraction). In practice, `STOP`, action prefix, external
and internal choice, general parallel, hiding, renaming, and prefix
choice/replicated internal choice (for infinite branching) form the
irreducible core that Chapter 3's own operational-semantics discussion
(Sec. 3.2.2) and this repo's [CSP toolkit](The%20Process%20Algebra%20CSP/main.py)
build directly on.

## B.3 Operational Semantics

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

## B.4 Denotational Semantics

Standard notations used throughout: Σ (alphabet of events), Σ✓ (Σ
extended with the termination event ✓), Σ*✓ (all non-terminating traces
over Σ), and (Σ*✓)⟨✓⟩ (all "interesting" traces — both non-terminating
and terminating ones).

### B.4.1 The Traces Model (T)

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

### B.4.2 The Failures/Divergences Model (N)

The denotation of P is a pair `(F, D)` of failures and divergences.
Healthiness conditions are named F1–F4 (on failures) and D1–D3 (on
divergences) — their exact formulas didn't survive extraction; Chapter
3's README (Sec. 3.4.1) explains the two that matter most in practice:
D1 (divergences are extension-closed) and D2 (divergent traces have all
possible failures). The domain is a complete partial order with bottom
element for finite alphabets.

### B.4.3 The Stable Failures Model (F)

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
