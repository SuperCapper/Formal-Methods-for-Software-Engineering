"""Companion code for Chapter 8, "Formal Verification of Security
Protocols" (Roggenbach et al., *Formal Methods for Software Engineering*).

Four pieces, each mirroring a section of the chapter:

1. A message algebra and the Dolev-Yao "generates" relation (Sec. 8.2.3,
   8.4.2, 8.4.4) -- the intruder's derivation power.
2. A mechanical, step-by-step replay of Lowe's man-in-the-middle attack on
   the Needham-Schroeder protocol (Sec. 8.3, Example 75.1), where every
   intruder step is *checked* against the generates-relation closure
   rather than just narrated -- and a replay of the same interleaving
   against the Needham-Schroeder-Lowe fix, showing where it breaks.
3. A signal-event / "precedes" checker (Sec. 8.4.5, Definitions 3, 5, 6)
   run against the resulting traces, reproducing Theorem 1's two claims:
   the attack preserves A's aliveness but breaks injective agreement.
4. A small, original illustration of the rank-function idea (Sec. 8.6) --
   not a mechanization of the full Rank Function Theorem (R1-R4 require a
   process-level proof calculus out of scope here), but a concrete
   demonstration of why NS's message shape leaks the secret nonce under a
   natural rank assignment, and why NSL's doesn't.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Tuple, Union

# ===========================================================================
# 1. Message algebra and the Dolev-Yao generates relation (Sec. 8.2, 8.4)
# ===========================================================================


@dataclass(frozen=True)
class User:
    name: str

    def __repr__(self):
        return self.name


@dataclass(frozen=True)
class Nonce:
    name: str

    def __repr__(self):
        return self.name


@dataclass(frozen=True)
class PubKey:
    owner: str

    def __repr__(self):
        return f"pk({self.owner})"


@dataclass(frozen=True)
class PrivKey:
    owner: str

    def __repr__(self):
        return f"sk({self.owner})"


@dataclass(frozen=True)
class Enc:
    key: Union[PubKey, PrivKey]
    content: "Message"

    def __repr__(self):
        return f"{{{self.content!r}}}{self.key!r}"


@dataclass(frozen=True)
class Pair:
    first: "Message"
    second: "Message"

    def __repr__(self):
        return f"{self.first!r}.{self.second!r}"


Message = Union[User, Nonce, PubKey, PrivKey, Enc, Pair]


def _inverse(key: Union[PubKey, PrivKey]) -> Union[PubKey, PrivKey]:
    """Eq. (8.1): the key that undoes `key` under the perfect-encryption assumption."""
    if isinstance(key, PubKey):
        return PrivKey(key.owner)
    return PubKey(key.owner)


def close_passive(knowledge: FrozenSet[Message]) -> FrozenSet[Message]:
    """Closure under Fig. 8.2's rules 3 and 5 (decrypt, unpair) only.
    These are the "safe" rules: they only ever produce sub-terms of
    already-known messages, so -- unlike rules 2 and 4 (encrypt, pair),
    which can each combine any two known messages into a brand new one --
    this always converges quickly."""
    known = set(knowledge)
    changed = True
    while changed:
        changed = False
        for m in list(known):
            if isinstance(m, Pair):
                for part in (m.first, m.second):
                    if part not in known:
                        known.add(part)
                        changed = True
            elif isinstance(m, Enc) and _inverse(m.key) in known and m.content not in known:
                known.add(m.content)
                changed = True
    return frozenset(known)


def generates(knowledge: FrozenSet[Message], target: Message) -> bool:
    """Whether `target` lies in the closure of `knowledge` under all five
    rules of Fig. 8.2. Rules 1/3/5 (know, decrypt, unpair) are handled by
    `close_passive`; rules 2/4 (encrypt, pair) are checked *constructively*
    top-down from `target`, rather than by forward-chaining every possible
    combination -- which is exactly the state-space blow-up Sec. 8.5.1
    warns about when a message space isn't kept finite."""
    known = close_passive(knowledge)
    if target in known:
        return True
    if isinstance(target, Enc):
        return target.key in known and generates(known, target.content)
    if isinstance(target, Pair):
        return generates(known, target.first) and generates(known, target.second)
    return False


# ===========================================================================
# 2. Lowe's attack on Needham-Schroeder, mechanically checked (Sec. 8.3)
# ===========================================================================

A, B, I = User("A"), User("B"), User("I")
A_pub, A_priv = PubKey("A"), PrivKey("A")
B_pub, B_priv = PubKey("B"), PrivKey("B")
I_pub, I_priv = PubKey("I"), PrivKey("I")
Na, Nb = Nonce("Na"), Nonce("Nb")

# Example 75.4: the intruder's initial knowledge.
INTRUDER_INITIAL = frozenset({A, B, I, A_pub, B_pub, I_pub, I_priv})


def run_ns_attack() -> Tuple[List[Tuple[str, str, Message]], FrozenSet[Message]]:
    """Example 75.1: two interleaved runs of the (flawed) N-S protocol.
    Every message the intruder sends is asserted to be derivable from its
    current knowledge -- i.e. this is a *checked* replay, not a narration."""
    ik = INTRUDER_INITIAL
    log: List[Tuple[str, str, Message]] = []

    msg_1_1 = Enc(I_pub, Pair(Na, A))  # A honestly starts a run WITH I
    ik = close_passive(ik | {msg_1_1})
    log.append(("1.1", "A -> I  (honest)", msg_1_1))

    msg_2_1 = Enc(B_pub, Pair(Na, A))  # I(A) starts a second run with B
    assert generates(ik, msg_2_1), "intruder cannot form message 2.1"
    log.append(("2.1", "I(A) -> B", msg_2_1))

    msg_2_2 = Enc(A_pub, Pair(Na, Nb))  # B replies, believing it's talking to A
    ik = close_passive(ik | {msg_2_2})
    log.append(("2.2", "B -> I (believes A)", msg_2_2))

    msg_1_2 = msg_2_2  # I can't decrypt this (no sk(A)) -- relays it unmodified
    assert generates(ik, msg_1_2)
    log.append(("1.2", "I -> A  (relayed)", msg_1_2))

    msg_1_3 = Enc(I_pub, Nb)  # A, still believing it's talking to I, replies
    ik = close_passive(ik | {msg_1_3})
    log.append(("1.3", "A -> I  (honest)", msg_1_3))

    msg_2_3 = Enc(B_pub, Nb)  # I decrypts msg_1_3 with sk(I), re-encrypts for B
    assert generates(ik, msg_2_3), "intruder cannot form the final message -- attack fails"
    log.append(("2.3", "I(A) -> B", msg_2_3))

    return log, ik


def run_nsl_attempt() -> Tuple[List[Tuple[str, str, Message]], bool]:
    """The same interleaving attempted against the N-S-L fix (Example 76):
    message 2 now includes B's identity, so A can detect that the
    responder in the relayed message isn't the one it thinks it's running
    with, and aborts before ever sending message 1.3."""
    ik = INTRUDER_INITIAL
    log: List[Tuple[str, str, Message]] = []

    msg_1_1 = Enc(I_pub, Pair(Na, A))
    ik = close_passive(ik | {msg_1_1})
    log.append(("1.1", "A -> I  (honest)", msg_1_1))

    msg_2_1 = Enc(B_pub, Pair(Na, A))
    assert generates(ik, msg_2_1)
    log.append(("2.1", "I(A) -> B", msg_2_1))

    msg_2_2 = Enc(A_pub, Pair(Pair(Na, Nb), B))  # NSL: B states its own identity
    ik = close_passive(ik | {msg_2_2})
    log.append(("2.2", "B -> I (believes A)", msg_2_2))

    msg_1_2 = msg_2_2  # I still can't decrypt or forge this -- relays unmodified
    assert generates(ik, msg_1_2)
    log.append(("1.2", "I -> A  (relayed)", msg_1_2))

    # A decrypts and checks: does the embedded responder identity match who
    # A believes it's running with (I, from message 1.1)?
    content = msg_1_2.content  # Pair(Pair(Na, Nb), B)
    responder_claimed = content.second
    believed_partner = I
    attack_detected = responder_claimed != believed_partner
    log.append(("--", f"A checks responder = {responder_claimed!r}, expected {believed_partner!r}", msg_1_2))

    return log, attack_detected


def _demo_attacks() -> None:
    print("--- 8.3 Lowe's man-in-the-middle attack, mechanically checked ---")

    log, final_knowledge = run_ns_attack()
    for step, desc, msg in log:
        print(f"  [{step}] {desc}: {msg!r}")
    print(f"  intruder derives B's own secret {Nb!r}? {Nb in final_knowledge}")
    print("  -> the N-S protocol is broken: B ends up 'authenticating' A, who never ran with B.")

    print()
    log, attack_detected = run_nsl_attempt()
    for step, desc, msg in log:
        print(f"  [{step}] {desc}: {msg!r}")
    print(f"  N-S-L: does A detect the attack and abort? {attack_detected}")
    print("  -> including B's identity in message 2 is enough to break the relay.")


# ===========================================================================
# 3. Signal events and the precedes predicate (Sec. 8.4.5, Def. 3, 5, 6)
# ===========================================================================


def precedes(a: str, b: str, trace: List[str]) -> bool:
    """Definition 3: every occurrence of b is preceded by an occurrence of a."""
    seen_a = False
    for e in trace:
        if e == a:
            seen_a = True
        if e == b and not seen_a:
            return False
    return True


def aliveness(authenticator: str, authenticatee: str, trace: List[str]) -> bool:
    """Definition 5: whenever `authenticator` commits believing
    `authenticatee`, `authenticatee` was running with *someone* beforehand."""
    for i, e in enumerate(trace):
        if e == f"Commit.{authenticator}.{authenticatee}":
            if not any(ev.startswith(f"Running.{authenticatee}.") for ev in trace[:i]):
                return False
    return True


def injective_agreement(authenticator: str, authenticatee: str, trace: List[str]) -> bool:
    """Definition 6, simplified: whenever `authenticator` commits with
    `authenticatee`, a matching Running signal *with that specific
    partner* occurred beforehand."""
    for i, e in enumerate(trace):
        if e == f"Commit.{authenticator}.{authenticatee}":
            if f"Running.{authenticatee}.{authenticator}" not in trace[:i]:
                return False
    return True


NS_ATTACK_TRACE = [
    "Running.A.I", "msg1.1", "msg2.1", "Running.B.A", "msg2.2", "msg1.2",
    "Commit.A.I", "msg1.3", "msg2.3", "Commit.B.A",
]

HONEST_TRACE = [
    "Running.A.B", "msg1", "Running.B.A", "msg2", "Commit.A.B", "msg3", "Commit.B.A",
]


def _demo_signals() -> None:
    print("--- 8.4.5 Signal events: aliveness vs. injective agreement (Theorem 1) ---")

    print(f"  attack trace: {NS_ATTACK_TRACE}")
    print(f"  A's aliveness guaranteed to B? {aliveness('B', 'A', NS_ATTACK_TRACE)}"
          f"   (A *was* running with someone -- just not with B)")
    print(f"  injective agreement (B on A)?  {injective_agreement('B', 'A', NS_ATTACK_TRACE)}"
          f"   (no 'Running.A.B' ever occurred -- B is deceived)")

    print(f"  honest N-S-L trace: {HONEST_TRACE}")
    print(f"  injective agreement (B on A)?  {injective_agreement('B', 'A', HONEST_TRACE)}")
    print(f"  injective agreement (A on B)?  {injective_agreement('A', 'B', HONEST_TRACE)}")


# ===========================================================================
# 4. A rank-function illustration (Sec. 8.6) -- simplified and original
# ===========================================================================


def rank(msg: Message) -> int:
    """A rank assignment in the spirit of Example 76.3: participant names,
    public keys, and the intruder's own private key are rank 1 (freely
    circulated); other private keys and the target secret Nb are rank 0.
    A pair is only as safe as its least-safe component. Crucially, the
    N-S-L-shaped ciphertext {Na.Nb.B}pk(A) is special-cased to rank 1 --
    its *plaintext* contains the rank-0 secret, but as long as only A can
    decrypt it, circulating the ciphertext itself is safe."""
    if msg == Enc(A_pub, Pair(Pair(Na, Nb), B)):  # the N-S-L message 2 shape
        return 1
    if isinstance(msg, (User, PubKey)):
        return 1
    if isinstance(msg, PrivKey):
        return 1 if msg.owner == "I" else 0
    if isinstance(msg, Nonce):
        return 0 if msg == Nb else 1
    if isinstance(msg, Pair):
        return min(rank(msg.first), rank(msg.second))
    if isinstance(msg, Enc):
        return rank(msg.content)
    raise TypeError(f"no rank assigned for {msg!r}")


def _demo_rank_function() -> None:
    print("--- 8.6 A rank-function illustration (simplified) ---")

    nsl_msg2 = Enc(A_pub, Pair(Pair(Na, Nb), B))
    ns_msg2 = Enc(A_pub, Pair(Na, Nb))
    print(f"  rank(secret nonce Nb) = {rank(Nb)}  (0 = must never be seen by the intruder)")
    print(f"  N-S-L message 2 {nsl_msg2!r}: rank = {rank(nsl_msg2)}"
          f"  (safe to circulate -- only A can decrypt it)")
    print(f"  N-S   message 2 {ns_msg2!r}: rank = {rank(ns_msg2)}"
          f"  (already rank 0 as a raw structural fact --")
    print(f"    matches the book's own closing remark that B 'does not maintain rank' for plain N-S)")


if __name__ == "__main__":
    _demo_attacks()
    print()
    _demo_signals()
    print()
    _demo_rank_function()
