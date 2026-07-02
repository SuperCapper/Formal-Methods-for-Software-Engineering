# Formal Methods

Companion notes/code for Chapter 1, "Formal Methods", of Roggenbach,
Cerone, Schlingloff, Schneider & Shaikh, *Formal Methods for Software
Engineering* (Springer, 2022) — see the top-level [README.md](../README.md)
for the course as a whole. Per the request that produced this companion,
**Sec. 1.4.1 "Current Research Directions" is intentionally excluded**
from these notes.

`main.py` implements the chapter's own running case study for what a
Formal Method actually *is* — regular expressions (Example 2 and its
sub-examples) — the one part of this introductory chapter that is
genuinely algorithmic. Run it with `python "main.py"` from this folder
(see [Environment](#environment) below).

## 1.1 What is a Formal Method?

Opens with two motivating examples before attempting a definition:

- **The ISS Fault Tolerant Computer** (1.1.1): four redundant hardware
  boards run a Byzantine-agreement protocol (Lamport, Shostak, Pease) to
  reach consensus despite faulty/lying boards. The protocol's pseudocode
  was *proven correct* — but the Occam implementation still shipped with
  bugs: abstracting the code into CSP and model-checking it with FDR
  found **7 deadlocks and ~5 livelocks**, all in the message-exchange
  layer that the original correctness proof never covered. The lesson:
  proving one layer correct (the algorithm) says nothing about layers the
  proof didn't model (the communication substrate) — see [Chapter 3's
  companion notes and CSP toolkit](../The%20Process%20Algebra%20CSP/) for
  the deadlock/livelock machinery this case study depends on.
- **Text processing / regular expressions** (1.1.2): the chapter's real
  running example. Word and GNU Emacs *disagree* about what `*` even
  means (replacing `*` with `x` in `"abc"` gives `"xxxx"` in Word but
  `"abc"` — i.e. no match — in Emacs, while Emacs' `.*` gives `"x"`),
  because neither tool's documentation gives `*` a precise mathematical
  semantics. This motivates **Definition 1**: a Formal Method consists of
  three components —
  - **Syntax**: a precise grammar (here, the regex grammar, Example 2.2:
    `E ::= a | ∅ | E.E | E+E | E*`, plus abbreviations like `E+`, `.`,
    `Σ*`, `E?`, `E^n`, `E^{m,n}`);
  - **Semantics**: a mapping from syntax into some mathematical
    structure — the chapter distinguishes **denotational** (an object
    denotes something in a semantic domain — Example 2.4: a regex
    denotes the *language* it matches), **operational** (execution by a
    virtual machine — Example 2.5: a regex compiles to an automaton), and
    **axiomatic** (a proof calculus for equalities — Example 2.6:
    Salomaa's axioms for regex equivalence, correct and — harder to show
    — complete);
  - **Method**: algorithms that transform syntactic objects into
    insight — Example 2.7 gives a fully formal definition of *regular
    replacement* (leftmost match, then longest match at that position),
    finally resolving Example 2.1's Word/Emacs ambiguity with a single,
    tool-independent answer.

`main.py` implements exactly this: a regex AST (`Letter`, `Eps`,
`EmptySet`, `Concat`, `Union`, `Star`), a denotational semantics
(`in_language()`, a direct membership test against Example 2.4's
clauses), an operational semantics (`to_nfa()`/`accepts()`, a Thompson-
style automaton construction following Example 2.5's rules one-for-one),
and `_demo_semantics_agree()`, which checks — rather than just asserts —
the book's own claim that "denotational and operational semantics
coincide." A handful of standard algebraic laws (idempotence,
distributivity, `(E*)* = E*`, the roles of `∅`/`ε`) are checked against
the denotational semantics by bounded enumeration, in the spirit of
Example 2.6 (though not a transcription of Salomaa's exact axiom list,
whose specific equations didn't survive extraction from the source).
Finally, `find_leftmost_longest_match()`/`replace()` implement Example
2.7's formal regular replacement directly, and reproduce both the book's
own resolution of the Word/Emacs disagreement *and* the classic
`<!--.*-->`-across-multiple-comments greedy-matching pitfall the chapter
opens with — verified by running it: replacing `<!-- one --> middle
<!-- two -->` with a naive "any character" body wildcard deletes both
comments *and* the text between them, exactly the bug precise semantics
is meant to let you predict (and avoid) in advance.

## 1.2 Formal Methods in software development

- **1.2.1 The software life cycle**: contrasts the sequential
  **waterfall model** (each phase strictly follows the last) with the
  **V-model** (esp. the V-Model XT, mandatory for safety-critical German
  government projects) which pairs each specification level
  (requirements → design → architecture → implementation) with a
  corresponding realisation/integration level, making **validation**
  ("are we building the right product?") and **verification** ("are we
  building the product right?") explicit, separate concerns. **Agile
  development** (small teams, short iterations, test-driven development,
  Scrum) is presented as the modern alternative — the chapter's point is
  that Formal Methods fit into *either* model; they aren't tied to
  heavyweight, phase-based processes.
- **1.2.2 When and where**: safety standards (IEC 61508, DO-333, EN-50128)
  increasingly *require or recommend* Formal Methods at the highest
  integrity levels (e.g. IEC 61508's SIL 4: provably fewer than one
  dangerous failure per 10,000 years of operation). Formal Methods serve
  **two purposes**: making descriptions *precise* (resolving the kind of
  linguistic/domain ambiguity real requirements documents are full of —
  "the product shall show the weather for the next 24 hours" is
  genuinely ambiguous about what the time window attaches to), and
  supporting *analysis* (static analysis, model checking, theorem
  proving, runtime verification) — this book focuses mostly on the
  second.
- **1.2.3 A classification scheme**: any Formal Method can be located
  along several independent dimensions beyond just "syntax, semantics,
  method" — syntactic style, semantic style, algorithmic approach
  (simulation, model checking, theorem proving, static analysis...),
  application domain, underlying technology (SAT solving, term
  rewriting...), properties of concern (safety, liveness, security...),
  and maturity/tool support. The chapter classifies both its own running
  examples this way (the ISS case study: CSP + failures semantics +
  refinement checking via FDR's state-compression technology, targeting
  deadlock/livelock in fault-tolerant aerospace algorithms; regular
  expressions: denotational set-theoretic semantics + text transformation,
  no specific technology, undergraduate-standard).
- **1.2.4 Tool support**: Formal Methods need tools for reasons that
  don't apply to pure mathematics — real specifications have *orders of
  magnitude* more axioms than a mathematical theory (a railway
  interlocking: 500–1,500 CASL axioms, vs. group theory's 3 axioms);
  software artefacts are usually *proprietary* (studied by few people,
  rarely), unlike published mathematical proofs (studied by many, over
  and over); and software's axiomatic basis *changes* every decade,
  unlike group theory's (stable since the 1830s). This raises **tool
  qualification**: who verifies the verifier? Real compiler bugs (GCC
  silently miscompiling valid code) and static-analysis tool bugs
  (Cppcheck false positives *and* false negatives, in the same program)
  motivate cross-checking multiple independent tools against each other,
  and augmenting theorem provers with independently-checkable proof
  certificates.

## 1.3 Formal Methods in practice

- **1.3.1 Comparative surveys**: several classic case studies — a
  production cell, an RPC memory cell, a steam-boiler controller,
  invoicing software, the Mondex electronic purse, the CoCoME trading
  system, a flawed handshake security protocol — were each independently
  tackled by a dozen-plus different Formal Methods, with the studies'
  own conclusion consistently being that *no single method dominates*;
  suitability is context-dependent, much like choosing a programming
  language.
- **1.3.2 Industrial practice**: "yesterday's Formal Methods are today's
  best practice" — static analysis (descended from 1970s abstract
  interpretation) is now standard in ordinary compilers; hardware model
  checking and theorem proving are established practice since the 1990s.
  Real success stories: **Intel** moved to full formal verification of
  floating-point units after the 1994 Pentium FDIV bug cost ~$475M;
  **Microsoft**'s Winterop project formally modelled 30,000 pages of
  protocol documentation, finding 10,000+ documentation issues and
  turning the effort into a shipping product (SpecExplorer); **seL4**
  and **PikeOS** are formally verified microkernels in real avionics use;
  **SCADE**, evolved from the academic language Lustre, is qualified to
  the highest aerospace criticality level and used across Airbus,
  Eurocopter, and nuclear plant control; the Paris Métro Line 14 and
  several other French transit systems were built with the **B method**
  and have run bug-free in production for decades.
- **1.3.3 How to get started**: for learners, the chapter recommends a
  case-study-driven approach — formalise, check the formalisation is
  faithful, derive properties *manually* first (by hand, using the
  semantics or a calculus), and only then reproduce the result with
  tools (so tool limitations don't quietly narrow your understanding of
  the method). For industrial adoption, a tool needs to be *supported*,
  *documented*, *integrable* into existing processes, and its use
  *predictable* — and even then, a pilot project should precede full
  adoption.

## 1.4 Closing remarks

Recaps the chapter's core: syntax (usually BNF), semantics (denotational,
operational, or axiomatic), and method are the three ingredients of any
Formal Method; they're useful in both classical and agile development;
international standards increasingly recognise and require them; and
real tool support is a precondition for real-world use.

*(Sec. 1.4.1, "Current Research Directions," is excluded from these
notes per the request that produced this companion.)*

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
python "Formal Methods/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
