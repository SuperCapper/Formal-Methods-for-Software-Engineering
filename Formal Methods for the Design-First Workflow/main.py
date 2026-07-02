"""Companion code tying this repo's Formal Methods chapters to the
Design-First workflow (design.md -> requirements.md -> tasks.md ->
implementation): a small toolkit that formally analyses the two
artefacts most amenable to it -- the architecture produced in the Design
phase, and the EARS-format requirements derived from it.

Unlike the other folders in this repo, this one is *not* extracted from
the textbook -- it's an original synthesis showing how techniques from
several chapters compose into practical tooling for this workflow:

1. An EARS requirements parser + translation to LTL (Chapter 2's logic,
   Chapter 5's LTL runtime-monitor style), so acceptance criteria written
   during the Requirements phase can be checked against a simulated or
   real execution trace of the implementation -- the same technique
   Chapter 5 uses for the VCR switch's "no card is inserted until cash
   is collected" property.
2. A requirement-conflict checker (Chapter 6's CL-style obligation/
   prohibition conflict analysis, Definition 1's four conflict cases),
   applied to EARS requirements instead of legal clauses -- catching
   contradictory SHALL/SHALL-NOT requirements before they reach the
   Tasks phase.
3. An architecture "waits-for" graph deadlock checker (Chapter 3's CSP
   deadlock analysis, generalised from process synchronisation to
   synchronous service calls), applied during the Design phase to catch
   circular-dependency deadlocks -- including the specifically
   AI-engineering-flavoured case of two agents each synchronously
   awaiting the other's tool call.

See the README in this folder for the full mapping from each of the
book's eight chapters to a stage of the Design-First workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ===========================================================================
# 1. EARS requirements: parsing and translation to LTL
# ===========================================================================
#
# EARS ("Easy Approach to Requirements Syntax") patterns, tried most
# specific first:
#   WHILE <state> WHEN <trigger> THE <system> SHALL <response>  (complex)
#   WHEN <trigger> THE <system> SHALL <response>                (event-driven)
#   WHILE <state> THE <system> SHALL <response>                 (state-driven)
#   IF <condition> THEN THE <system> SHALL <response>           (unwanted behaviour)
#   WHERE <feature> THE <system> SHALL <response>                (optional feature)
#   THE <system> SHALL <response>                                 (ubiquitous)

_EARS_PATTERNS: List[Tuple[str, "re.Pattern"]] = [
    ("complex", re.compile(
        r"^WHILE (?P<state>.+?) WHEN (?P<trigger>.+?) THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
    ("event", re.compile(
        r"^WHEN (?P<trigger>.+?) THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
    ("state", re.compile(
        r"^WHILE (?P<state>.+?) THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
    ("unwanted", re.compile(
        r"^IF (?P<condition>.+?) THEN THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
    ("optional", re.compile(
        r"^WHERE (?P<feature>.+?) THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
    ("ubiquitous", re.compile(
        r"^THE (?P<system>.+?) SHALL (?P<response>.+)$", re.I)),
]


def _atom(text: str) -> str:
    """Normalise free text into an LTL-atom-friendly identifier."""
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


@dataclass(frozen=True)
class Requirement:
    id: str
    raw: str
    kind: str
    system: str
    response: str
    negated: bool  # True if response was "SHALL NOT ..."
    condition: Optional[str] = None  # trigger / state / condition / feature, normalised

    @property
    def response_atom(self) -> str:
        return _atom(self.response)

    @property
    def condition_atom(self) -> Optional[str]:
        return _atom(self.condition) if self.condition else None


def parse_ears(req_id: str, text: str) -> Requirement:
    text = text.strip().rstrip(".")
    for kind, pattern in _EARS_PATTERNS:
        m = pattern.match(text)
        if not m:
            continue
        groups = m.groupdict()
        response = groups["response"]
        negated = bool(re.match(r"^NOT\b", response, re.I))
        if negated:
            response = re.sub(r"^NOT\s+", "", response, flags=re.I)
        condition = groups.get("trigger") or groups.get("state") or groups.get("condition") or groups.get("feature")
        return Requirement(req_id, text, kind, groups["system"], response, negated, condition)
    raise ValueError(f"'{text}' does not match any EARS pattern")


# --- LTL, self-contained (same small toolkit as Chapters 2 and 5) ----------


class LTL:
    pass


@dataclass(frozen=True)
class Prop(LTL):
    name: str


@dataclass(frozen=True)
class Not(LTL):
    inner: LTL


@dataclass(frozen=True)
class Implies(LTL):
    left: LTL
    right: LTL


@dataclass(frozen=True)
class Always(LTL):
    inner: LTL


@dataclass(frozen=True)
class Eventually(LTL):
    inner: LTL


Trace = Tuple[str, ...]


def eval_ltl(f: LTL, trace: Trace, i: int) -> bool:
    if isinstance(f, Prop):
        return i < len(trace) and trace[i] == f.name
    if isinstance(f, Not):
        return not eval_ltl(f.inner, trace, i)
    if isinstance(f, Implies):
        return (not eval_ltl(f.left, trace, i)) or eval_ltl(f.right, trace, i)
    if isinstance(f, Always):
        return all(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    if isinstance(f, Eventually):
        return any(eval_ltl(f.inner, trace, j) for j in range(i, len(trace)))
    raise TypeError(f"unknown LTL node: {f!r}")


def check(f: LTL, trace: List[str]) -> bool:
    return eval_ltl(f, tuple(trace), 0)


def to_ltl(req: Requirement) -> LTL:
    """A default, documented translation from each EARS pattern to LTL --
    a starting point for acceptance-criteria checking, not a universal
    semantics (the right operator, e.g. Eventually vs. Next, ultimately
    depends on the specific requirement's intended timing)."""
    response = Not(Prop(req.response_atom)) if req.negated else Prop(req.response_atom)
    if req.kind == "ubiquitous":
        return Always(response)
    if req.kind == "event":
        return Always(Implies(Prop(req.condition_atom), Eventually(response)))
    if req.kind == "state":
        return Always(Implies(Prop(req.condition_atom), response))
    if req.kind == "unwanted":
        return Always(Implies(Prop(req.condition_atom), Eventually(response)))
    if req.kind == "optional":
        return Implies(Prop(req.condition_atom), Always(response))
    if req.kind == "complex":
        return Always(response)  # simplified: state-guarding omitted for brevity
    raise ValueError(f"unknown EARS kind: {req.kind}")


# ===========================================================================
# 2. Requirement-conflict checking (Chapter 6's CL-style conflict analysis)
# ===========================================================================


def find_conflicts(reqs: List[Requirement], mutually_exclusive: Set[frozenset] = frozenset()) -> List[Tuple[Requirement, Requirement, str]]:
    """Flags pairs of requirements that are triggered by the same
    condition but mandate contradictory responses -- Definition 1's
    conflict cases (i)/(iii) from Chapter 6, applied to requirements
    instead of contract clauses: same trigger, SHALL vs. SHALL NOT on the
    same response (a direct contradiction), or SHALL on two responses
    declared mutually exclusive."""
    conflicts = []
    for i, r1 in enumerate(reqs):
        for r2 in reqs[i + 1:]:
            if r1.condition_atom is None or r1.condition_atom != r2.condition_atom:
                continue
            if r1.response_atom == r2.response_atom and r1.negated != r2.negated:
                conflicts.append((r1, r2, "same trigger, contradictory SHALL/SHALL NOT on the same response"))
            elif not r1.negated and not r2.negated and frozenset({r1.response_atom, r2.response_atom}) in mutually_exclusive:
                conflicts.append((r1, r2, "same trigger, two declared mutually-exclusive responses both required"))
    return conflicts


# ===========================================================================
# 3. Architecture deadlock checking (Chapter 3's CSP deadlock analysis,
#    generalised to a synchronous-call "waits-for" graph)
# ===========================================================================


@dataclass
class Architecture:
    """A synchronous call graph: `calls[A]` is the set of components A
    blocks on while waiting for a response -- exactly the "waits-for"
    relation whose cycles are deadlocks, the same structural condition
    Chapter 3's CSP model checks for synchronous parallel composition."""

    calls: Dict[str, Set[str]] = field(default_factory=dict)

    def add_call(self, caller: str, callee: str) -> None:
        self.calls.setdefault(caller, set()).add(callee)
        self.calls.setdefault(callee, set())


def find_deadlock_cycle(arch: Architecture) -> Optional[List[str]]:
    """DFS cycle detection on the waits-for graph. A cycle means every
    component on it is (transitively) waiting on itself -- a deadlock,
    regardless of what each component actually does."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {n: WHITE for n in arch.calls}
    path: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        colour[node] = GREY
        path.append(node)
        for nxt in sorted(arch.calls.get(node, ())):
            if colour[nxt] == GREY:
                cycle_start = path.index(nxt)
                return path[cycle_start:] + [nxt]
            if colour[nxt] == WHITE:
                result = visit(nxt)
                if result:
                    return result
        path.pop()
        colour[node] = BLACK
        return None

    for node in sorted(arch.calls):
        if colour[node] == WHITE:
            result = visit(node)
            if result:
                return result
    return None


# ===========================================================================
# Demo 1 (software engineering): the notification-system example
# ===========================================================================


def _demo_notification_system() -> None:
    print("--- Design phase: notification-system architecture (deadlock check) ---")

    good = Architecture()
    good.add_call("APIGateway", "Lambda")
    good.add_call("Lambda", "DynamoDB")
    good.add_call("Lambda", "SQS")
    cycle = find_deadlock_cycle(good)
    print(f"  APIGateway -> Lambda -> {{DynamoDB, SQS}}: deadlock cycle? {cycle}")

    bad = Architecture()
    bad.add_call("APIGateway", "Lambda")
    bad.add_call("Lambda", "DynamoDB")
    bad.add_call("Lambda", "EnrichmentService")
    bad.add_call("EnrichmentService", "Lambda")  # synchronous call-back -- circular wait
    cycle = find_deadlock_cycle(bad)
    print(f"  ...with a synchronous callback Lambda <-> EnrichmentService: deadlock cycle? {cycle}")
    print("  (a real design smell: fix by making the callback async, or breaking the cycle)")

    print()
    print("--- Requirements phase: EARS requirements derived from the design ---")

    texts = {
        "R1": "WHEN a message is published THE System SHALL deliver it to connected clients",
        "R2": "WHILE a user is offline THE System SHALL persist the message for later delivery",
        "R3": "IF the WebSocket connection drops THEN THE System SHALL NOT lose queued messages",
        "R4": "WHEN a message is published THE System SHALL discard it immediately",  # deliberately conflicts with R1
    }
    reqs = [parse_ears(rid, t) for rid, t in texts.items()]
    for r in reqs:
        print(f"  {r.id} [{r.kind}]: condition={r.condition_atom!r} "
              f"response={'NOT ' if r.negated else ''}{r.response_atom!r}")

    conflicts = find_conflicts(reqs, mutually_exclusive={frozenset({"deliver_it_to_connected_clients", "discard_it_immediately"})})
    print(f"  conflicts found: {len(conflicts)}")
    for r1, r2, reason in conflicts:
        print(f"    {r1.id} vs {r2.id}: {reason}")

    print()
    print("--- Checking R1 as an LTL acceptance criterion against a simulated trace ---")
    r1_ltl = to_ltl(reqs[0])
    good_trace = ["a_message_is_published", "deliver_it_to_connected_clients"]
    bad_trace = ["a_message_is_published", "internal_error"]
    print(f"  R1 as LTL: G(a_message_is_published -> F(deliver_it_to_connected_clients))")
    print(f"  trace {good_trace}: satisfies R1? {check(r1_ltl, good_trace)}")
    print(f"  trace {bad_trace}: satisfies R1? {check(r1_ltl, bad_trace)}")


# ===========================================================================
# Demo 2 (AI engineering): a multi-agent tool-calling architecture
# ===========================================================================


def _demo_multi_agent_system() -> None:
    print("--- Design phase: multi-agent architecture (deadlock check) ---")

    arch = Architecture()
    arch.add_call("Orchestrator", "ResearchAgent")
    arch.add_call("Orchestrator", "WriterAgent")
    arch.add_call("ResearchAgent", "SearchTool")
    arch.add_call("WriterAgent", "ResearchAgent")   # writer waits on researcher for facts
    arch.add_call("ResearchAgent", "WriterAgent")   # researcher waits on writer to phrase a sub-query -- cycle!
    cycle = find_deadlock_cycle(arch)
    print(f"  Orchestrator -> {{ResearchAgent, WriterAgent}}, with ResearchAgent <-> WriterAgent")
    print(f"  synchronously awaiting each other: deadlock cycle? {cycle}")
    print("  (a genuinely common agentic-system bug: two agents each blocked on a synchronous")
    print("   call to the other -- invisible in a sequence diagram, obvious once modelled as a graph)")

    print()
    print("--- Requirements phase: EARS-style agent behaviour policy (Chapter 6-style conflict) ---")

    texts = {
        "P1": "IF a tool call would delete data THEN THE Agent SHALL request user confirmation",
        "P2": "WHEN the user has enabled autonomous mode THE Agent SHALL request user confirmation",
        "P3": "WHEN the user has enabled autonomous mode THE Agent SHALL skip confirmation prompts",  # conflicts with P2
    }
    reqs = [parse_ears(rid, t) for rid, t in texts.items()]
    for r in reqs:
        print(f"  {r.id} [{r.kind}]: condition={r.condition_atom!r} "
              f"response={'NOT ' if r.negated else ''}{r.response_atom!r}")

    conflicts = find_conflicts(
        reqs,
        mutually_exclusive={frozenset({"request_user_confirmation", "skip_confirmation_prompts"})},
    )
    print(f"  conflicts found: {len(conflicts)}")
    for r1, r2, reason in conflicts:
        print(f"    {r1.id} vs {r2.id}: {reason}")
    print("  (P1 and P2 alone are each reasonable -- confirm on data deletion, confirm in")
    print("   autonomous mode -- but P3 was likely added later for UX reasons and directly")
    print("   contradicts P2 on the same trigger: exactly the kind of interaction-effect conflict")
    print("   Chapter 6's Example 57 warns is easy to miss one requirement at a time)")


if __name__ == "__main__":
    _demo_notification_system()
    print()
    _demo_multi_agent_system()
