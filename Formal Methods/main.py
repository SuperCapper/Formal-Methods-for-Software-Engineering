"""Companion code for Chapter 1, "Formal Methods" (Roggenbach et al.,
*Formal Methods for Software Engineering*).

The chapter's own running case study for what a Formal Method *is* --
syntax, semantics, and method (Definition 1) -- is regular expressions
(Example 2 and its sub-examples). This is the one part of the chapter
that is genuinely algorithmic, so it's what this file implements:

1. A regex AST (Example 2.2's syntax) with two semantics that the book
   claims *coincide*: a denotational semantics (Example 2.4, "what
   language does this expression denote?") and an operational semantics
   (Example 2.5, "what automaton does this expression compile to?").
   `_demo_semantics_agree()` checks this claim directly.
2. A handful of standard regular-expression algebraic laws, checked
   (bounded, by enumeration) against the denotational semantics -- in the
   spirit of Example 2.6's axiomatic semantics, though not a transcription
   of Salomaa's exact axiom list (garbled in extraction).
3. Formal "regular replacement" (Example 2.7): a precise, tool-independent
   leftmost-longest-match substitution -- resolving the very ambiguity
   Example 2.1 catches Word and Emacs disagreeing on.
"""

from __future__ import annotations

import functools
import itertools
from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Set, Tuple

# ===========================================================================
# 1. Syntax (Example 2.2) and denotational semantics (Example 2.4)
# ===========================================================================


class Regex:
    pass


@dataclass(frozen=True)
class Letter(Regex):
    ch: str

    def __repr__(self):
        return self.ch


@dataclass(frozen=True)
class Eps(Regex):  # the empty word, epsilon
    def __repr__(self):
        return "eps"


@dataclass(frozen=True)
class EmptySet(Regex):  # the regex matching nothing, "0"
    def __repr__(self):
        return "0"


@dataclass(frozen=True)
class Concat(Regex):
    left: Regex
    right: Regex

    def __repr__(self):
        return f"{self.left!r}{self.right!r}"


@dataclass(frozen=True)
class Union(Regex):
    left: Regex
    right: Regex

    def __repr__(self):
        return f"({self.left!r}+{self.right!r})"


@dataclass(frozen=True)
class Star(Regex):
    inner: Regex

    def __repr__(self):
        return f"({self.inner!r})*"


@functools.lru_cache(maxsize=None)
def in_language(e: Regex, w: str) -> bool:
    """Denotational semantics (Example 2.4): is w in L(e)?"""
    if isinstance(e, Letter):
        return w == e.ch
    if isinstance(e, Eps):
        return w == ""
    if isinstance(e, EmptySet):
        return False
    if isinstance(e, Concat):
        return any(in_language(e.left, w[:i]) and in_language(e.right, w[i:]) for i in range(len(w) + 1))
    if isinstance(e, Union):
        return in_language(e.left, w) or in_language(e.right, w)
    if isinstance(e, Star):
        if w == "":
            return True
        return any(
            in_language(e.inner, w[:i]) and in_language(e, w[i:])
            for i in range(1, len(w) + 1)
        )
    raise TypeError(f"unknown regex node: {e!r}")


# --- Abbreviations (Example 2.3) --------------------------------------------


def plus(e: Regex) -> Regex:
    """e+ := e.e* -- one or more repetitions."""
    return Concat(e, Star(e))


def opt(e: Regex) -> Regex:
    """e? := e + eps -- maybe one e."""
    return Union(e, Eps())


def lit(s: str) -> Regex:
    """A literal multi-character string, as a chain of concatenations."""
    if not s:
        return Eps()
    result: Regex = Letter(s[0])
    for ch in s[1:]:
        result = Concat(result, Letter(ch))
    return result


def any_of(alphabet: str) -> Regex:
    """The "any single letter" wildcard over a finite alphabet."""
    letters = [Letter(c) for c in alphabet]
    result = letters[0]
    for l in letters[1:]:
        result = Union(result, l)
    return result


# ===========================================================================
# 2. Operational semantics (Example 2.5): compiling a regex to an automaton
# ===========================================================================


@dataclass
class NFA:
    nodes: Set[int]
    edges: List[Tuple[int, Optional[str], int]]  # (from, label-or-None-for-tau, to)
    initial: int
    finals: Set[int]


def to_nfa(e: Regex, counter: Optional[itertools.count] = None) -> NFA:
    """Thompson-style construction, following Example 2.5's rules exactly:
    one rule per syntax case, building the automaton compositionally."""
    counter = counter or itertools.count()
    if isinstance(e, Letter):
        s, f = next(counter), next(counter)
        return NFA({s, f}, [(s, e.ch, f)], s, {f})
    if isinstance(e, Eps):
        n = next(counter)
        return NFA({n}, [], n, {n})
    if isinstance(e, EmptySet):
        n = next(counter)
        return NFA({n}, [], n, set())
    if isinstance(e, Concat):
        a = to_nfa(e.left, counter)
        b = to_nfa(e.right, counter)
        edges = a.edges + b.edges + [(f, None, b.initial) for f in a.finals]
        return NFA(a.nodes | b.nodes, edges, a.initial, b.finals)
    if isinstance(e, Union):
        a = to_nfa(e.left, counter)
        b = to_nfa(e.right, counter)
        s = next(counter)
        edges = a.edges + b.edges + [(s, None, a.initial), (s, None, b.initial)]
        return NFA(a.nodes | b.nodes | {s}, edges, s, a.finals | b.finals)
    if isinstance(e, Star):
        a = to_nfa(e.inner, counter)
        s = next(counter)
        edges = a.edges + [(s, None, a.initial)] + [(f, None, s) for f in a.finals]
        return NFA(a.nodes | {s}, edges, s, {s})
    raise TypeError(f"unknown regex node: {e!r}")


def _eps_closure(nfa: NFA, states: Set[int]) -> Set[int]:
    seen = set(states)
    stack = list(states)
    while stack:
        n = stack.pop()
        for a, label, b in nfa.edges:
            if a == n and label is None and b not in seen:
                seen.add(b)
                stack.append(b)
    return seen


def accepts(nfa: NFA, w: str) -> bool:
    """A word is accepted if there's a path from the initial node to some
    final node labelled by w (Example 2.5)."""
    current = _eps_closure(nfa, {nfa.initial})
    for ch in w:
        nxt = set()
        for a, label, b in nfa.edges:
            if a in current and label == ch:
                nxt.add(b)
        current = _eps_closure(nfa, nxt)
    return bool(current & nfa.finals)


def _demo_semantics_agree() -> None:
    print("--- Example 2.4 vs 2.5: denotational and operational semantics coincide ---")

    a, b, c = Letter("a"), Letter("b"), Letter("c")
    cases = [
        Concat(a, Star(b)),                     # a.b*
        Union(a, b),                             # a+b
        plus(a),                                 # a+ = a.a*
        Concat(Concat(a, b), Star(Union(a, b))), # ab(a+b)*
        Star(Concat(a, b)),                      # (ab)*
    ]
    test_words = ["", "a", "b", "c", "ab", "ba", "abb", "aab", "abab", "aaab", "bbb"]

    all_agree = True
    for e in cases:
        nfa = to_nfa(e)
        for w in test_words:
            denotational = in_language(e, w)
            operational = accepts(nfa, w)
            if denotational != operational:
                all_agree = False
                print(f"  MISMATCH on {e!r}, word {w!r}: denotational={denotational} operational={operational}")
    print(f"  regex {[repr(e) for e in cases]}")
    print(f"  checked against words {test_words}")
    print(f"  denotational and operational semantics agree on every case? {all_agree}")


# ===========================================================================
# 3. Algebraic laws, checked against the denotational semantics
#    (in the spirit of Example 2.6's axiomatic semantics)
# ===========================================================================


def equivalent_upto(e1: Regex, e2: Regex, alphabet: str, max_len: int) -> bool:
    """Bounded language-equivalence check: agree on every word up to
    max_len over the given alphabet. Not a decision procedure for
    equivalence of infinite languages in general, but sufficient to
    demonstrate that a proposed algebraic law is at least not falsified
    on short words."""
    for length in range(max_len + 1):
        for tup in itertools.product(alphabet, repeat=length):
            w = "".join(tup)
            if in_language(e1, w) != in_language(e2, w):
                return False
    return True


def _demo_algebraic_laws() -> None:
    print("--- Example 2.6-style algebraic laws, checked against the denotational semantics ---")

    a, b, c = Letter("a"), Letter("b"), Letter("c")
    laws = [
        ("E+E = E", Union(a, a), a),
        ("E+F = F+E", Union(a, b), Union(b, a)),
        ("E.(F+G) = E.F+E.G", Concat(a, Union(b, c)), Union(Concat(a, b), Concat(a, c))),
        ("(E*)* = E*", Star(Star(a)), Star(a)),
        ("E+0 = E", Union(a, EmptySet()), a),
        ("E.eps = E", Concat(a, Eps()), a),
        ("E.0 = 0", Concat(a, EmptySet()), EmptySet()),
    ]
    for name, lhs, rhs in laws:
        holds = equivalent_upto(lhs, rhs, alphabet="abc", max_len=5)
        print(f"  {name}: holds (words up to length 5 over {{a,b,c}})? {holds}")


# ===========================================================================
# 4. Formal regular replacement (Example 2.7), resolving Example 2.1
# ===========================================================================


def find_leftmost_longest_match(e: Regex, s: str) -> Optional[Tuple[str, str, str]]:
    """The formal reading of Example 2.7: find the leftmost position in s
    where e matches at all, then the longest match starting there.
    Returns (u, v, w) with s = u + v + w and v in L(e), or None."""
    n = len(s)
    for start in range(n + 1):
        for end in range(n, start - 1, -1):
            v = s[start:end]
            if in_language(e, v):
                return s[:start], v, s[end:]
    return None


def replace(e: Regex, replacement: str, s: str) -> str:
    match = find_leftmost_longest_match(e, s)
    if match is None:
        return s
    u, v, w = match
    return f"{u}{replacement}{w}"


ALPHABET = "abcdefghijklmnopqrstuvwxyz"
ANY_WORD = Star(any_of(ALPHABET + " <!->"))  # Sigma*, used for HTML-comment stripping below


def _demo_regular_replacement() -> None:
    print("--- Example 2.7: formal regular replacement resolves Example 2.1's ambiguity ---")

    # Sigma* over {a,b,c}, matching the book's own "any word" reading of '*'.
    sigma_star = Star(any_of("abc"))
    result = replace(sigma_star, "x", "abc")
    print(f"  replace(Sigma*, 'x', 'abc') = {result!r}")
    print(f"  matches the book's own conclusion (u=eps, v='abc', w=eps) -- and GNU Emacs' '.*' behaviour,")
    print(f"  not Word's tool-specific quirk of inserting 'x' between every character (Example 2.1)")

    # The chapter's own opening motivating example: stripping HTML comments.
    comment = Concat(Concat(lit("<!--"), Star(any_of(ALPHABET + " <!->"))), lit("-->"))
    html = "keep <!-- drop this --> keep"
    print(f"  HTML comment example: replace({html!r}, '') = {replace(comment, '', html)!r}")

    # A classic greedy-matching gotcha: leftmost-longest across *two* comments
    # merges them, because the longest match starting at the first '<!--'
    # extends all the way to the *last* '-->' in the string.
    html_two_comments = "keep <!-- one --> middle <!-- two --> keep"
    print(f"  two separate comments: replace({html_two_comments!r}, '') =")
    print(f"    {replace(comment, '', html_two_comments)!r}")
    print("    (both comments AND the text between them vanish -- the classic")
    print("     '.*' greedy-matching pitfall the chapter opens with)")


if __name__ == "__main__":
    _demo_semantics_agree()
    print()
    _demo_algebraic_laws()
    print()
    _demo_regular_replacement()
