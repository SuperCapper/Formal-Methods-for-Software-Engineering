# Appendix C — Concrete CASL Syntax

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

## Notational Conventions (stated explicitly in the appendix)

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

## C.1 Specifications

The top-level grammar for a CASL specification (`spec NAME = BASIC-SPEC
end`, with `then`/`and` for extension/union — see Chapter 4, Sec.
4.4.1–4.4.2 for the worked examples this grammar underpins). The
appendix's own production rules for this section were not recoverable
from the source; see Chapter 4's [`main.py`](Algebraic%20Specification%20in%20CASL/main.py)
for a signature-level (`extension`/`union`/`rename`) implementation of
the corresponding semantics.

## C.2 Signature Declarations

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

## C.3 Formulae

Extends `BASIC-ITEMS` with constructs for writing axioms — quantified
first-order formulae over the declared signature, following `%(label)%`
conventions for naming axioms (see Chapter 4, Example 43.2's `%(name_
found)%`-style labelled axioms) and the `%implies`/`%cons`/`%def`
annotations for expressing proof obligations about an extension (Chapter
4, Sec. 4.3.2, Definition 5).

## C.4 Sort Generation Constraints

Extends `BASIC-ITEMS` with the `generated`/`free` type constructs (see
Chapter 4, Example 43.7's `free type` usage) — syntactic sugar for the
second-order term-generatedness properties discussed in Chapter 2, Sec.
2.4.2 (Definitions 17–18).

---

See also: [Chapter 4 companion notes and code](Algebraic%20Specification%20in%20CASL/) for a
worked reference implementation of a CASL specification (the Telephone
Database), a ConGu-style random axiom checker, and a signature-level
implementation of CASL's structuring operators.
