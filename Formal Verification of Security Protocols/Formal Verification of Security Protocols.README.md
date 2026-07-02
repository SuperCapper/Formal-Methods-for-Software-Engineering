# Formal Verification of Security Protocols

Companion notes/code for Chapter 8, "Formal Verification of Security
Protocols", of Roggenbach, Cerone, Schlingloff, Schneider & Shaikh,
*Formal Methods for Software Engineering* (Springer, 2022) — see the
top-level [README.md](../README.md) for the course as a whole.

`main.py` implements a message algebra with the Dolev-Yao "generates"
relation, then uses it to *mechanically check* — not just narrate — Gavin
Lowe's classic man-in-the-middle attack on the Needham-Schroeder protocol,
plus a signal-event authentication checker and a small rank-function
illustration. Run it with `python "main.py"` from this folder (see
[Environment](#environment) below).

## 8.1-8.2 Introduction and basic principles

Opens with Ali Baba's "Open Sesame" to illustrate three ideas that recur
throughout: **challenge-response** protocols, the ever-present threat of
**eavesdropping**, and the **perfect encryption assumption** — cryptography
itself is assumed unbreakable, so the chapter's whole focus is on
*protocol design* flaws, not cryptanalysis (a system can be completely
insecure even with unbreakable crypto, purely from how messages are
sequenced and structured).

- **Cryptography** (8.2.1): shared-key (same key encrypts/decrypts) vs.
  public-key (`pk`/`sk` pairs — Eq. 8.1: `dec(sk(A), enc(pk(A), m)) = m`
  for confidentiality; Eq. 8.2 the reverse, for signing). RSA is worked
  through as the running example, with a note that "textbook RSA" is
  itself insecure without padding (OAEP) — a reminder that the "perfect
  encryption" assumption is a deliberate abstraction, not a claim about
  real cryptosystems.
- **Security principles** (8.2.2): confidentiality, integrity,
  availability, and — this chapter's focus — **authentication** (data
  authentication: a message really came from who it claims; entity
  authentication: you're really talking to who you think you are).
- **Security protocols & the Dolev-Yao intruder** (8.2.3): a protocol is
  a fixed message-exchange sequence (`A -> B : m`, with `.` for
  concatenation). The standard adversary model gives the intruder the
  power to **block**, **replay**, **spoof**, **manipulate** (assemble/
  disassemble), and **encrypt/decrypt** — but only with keys it actually
  possesses. A first worked example (a session-key exchange) already
  falls to a man-in-the-middle attack that only needs this much power.

## 8.3 The Needham-Schroeder protocol

The chapter's central case study, walked through in three stages:

1. **N-S protocol** (1978): `A -> B: {Na.A}pk(B)`; `B -> A: {Na.Nb}pk(A)`;
   `A -> B: {Nb}pk(B)` — a challenge-response exchange of
   fresh **nonces** intended to give mutual **injective agreement**
   (Lowe's strongest guarantee: both parties are in the *same* run,
   agreeing on the same data, and each run is uniquely paired — vs. the
   weaker **aliveness**, which only confirms the other party has run the
   protocol *at some point*, with no guarantee about with whom).
2. **Lowe's attack** (1995), 17 years later: by interleaving *two*
   simultaneous runs — one where the intruder `I` honestly talks to `A`,
   one where `I` impersonates `A` to `B` — the intruder gets `A` itself
   to (unwittingly) decrypt and re-encrypt the pieces needed to complete
   an authentication with `B` that `A` never intended. `B` ends up fully
   convinced it just ran the protocol with `A`; `A` never even attempted
   to talk to `B`.
3. **N-S-L fix**: add the responder's identity into message 2 —
   `B -> A: {Na.Nb.B}pk(A)`. Now the relayed message carries proof of
   *which* run it came from, and `A` can detect the mismatch.

`main.py`'s `run_ns_attack()` and `run_nsl_attempt()` replay this exactly,
message by message, using the message algebra below to *assert* — not
assume — that each intruder step is actually derivable. Running it
prints the full 6-message attack trace and confirms the intruder ends up
knowing `B`'s own secret nonce; the N-S-L replay shows the same
interleaving attempt now caught at message 1.2, exactly where the
identity check fails.

## 8.4 Formal specification of protocols and properties

- **Data abstraction** (8.4.1): reduce the infinite space of real
  participants/keys/nonces down to two honest users and one intruder,
  one nonce per participant per run — a data abstraction assumed *sound
  and complete* (informally; the chapter notes this could in principle be
  proven with Lazić's data-independence techniques, but isn't here).
- **Message space** (8.4.2): a small grammar — atoms (users, nonces,
  keys), pairing, encryption — that's already infinite (nesting is
  unbounded), which becomes important in Sec. 8.5 when a *finite*
  approximation is needed for model checking.
- **CSP participants over a reliable network** (8.4.3), then **the
  Dolev-Yao intruder formalized in CSP** (8.4.4): the intruder's
  knowledge grows via a `generates` relation (Fig. 8.2) — five rules:
  know what you're told, encrypt/decrypt with a possessed key, pair/unpair.
  The intruder process is placed *in* the network, so it mediates every
  message — full control, matching Dolev-Yao's threat model exactly.
- **Signal events & instrumentation** (8.4.5): raw traces of
  encrypted messages don't show *beliefs* — you can't tell from the wire
  that `B` thinks it's talking to `A`. The fix is **instrumentation**:
  add `Running`/`Commit` signal events recording each participant's
  belief about who they're authenticating, then define aliveness and
  injective agreement as **`precedes`** properties over these signals
  (Definitions 3, 5, 6) — Commit must always be preceded by a matching
  Running.

`main.py`'s message algebra (`User`, `Nonce`, `PubKey`, `PrivKey`, `Enc`,
`Pair`) and `generates()` implement Fig. 8.2's five rules directly.
`generates()` is deliberately *not* a naive forward-chaining closure —
an earlier version of this file computed the full closure eagerly (pairing
and encrypting every combination of everything known) and it never
terminated in reasonable time, reproducing exactly the state-space
explosion Sec. 8.5.1 warns about. The fix mirrors the book's own:
`close_passive()` handles only the "safe", naturally-bounded rules
(decrypt, unpair — these only ever produce sub-terms of what's already
known), and `generates()` checks encrypt/pair *constructively*, top-down
from the target message, rather than by blind forward search.
`precedes()`, `aliveness()`, and `injective_agreement()` implement
Definitions 3, 5, 6 directly and are checked against both the attack
trace and an honest run — reproducing Theorem 1's two claims exactly:
A's aliveness survives the attack (A really was running *with someone*),
but injective agreement fails (never with B specifically).

## 8.5 Protocol analysis by model checking

Encoding this for FDR (via CSP-machine-readable syntax) needs three
"coding tricks" the chapter walks through in detail: (1) restrict the
message space to only what one protocol run could actually produce,
since the full grammar is infinite; (2) represent the intruder's
knowledge — a priori an exponential number of subsets of all facts — as
*many parallel processes* (one per fact, each either `Known` or
`Unknown`), turning the state explosion into something FDR's parallel-
process machinery is actually good at; (3) bound the intruder's inference
to finitely many steps (since there are only finitely many `Unknown` →
`Known` transitions possible). The payoff (**Theorem 1**): FDR finds the
N-S counterexample automatically (it's exactly Lowe's attack), and
confirms N-S-L is correct — *conditional* on the implemented inference
relation being complete with respect to Fig. 8.2's `generates` relation.

*Not implemented*: the actual CSP-machine-readable encoding (channels,
datatypes, the parallel-process knowledge representation) — `main.py`
gets the same underlying result (find the N-S attack, confirm N-S-L
resists it) via direct simulation in Python rather than by building a
CSP model and invoking FDR.

## 8.6 Protocol analysis by theorem proving

An alternative to model checking that sidesteps state-space explosion
entirely: **rank functions**. Assign every message (and signal) a rank
of 0 ("forbidden" — must never reach the intruder) or 1 ("safe to
circulate freely"). **Theorem 3** (the Rank Function Theorem): if a rank
function satisfies four conditions —

- **R1**: the intruder's initial knowledge is all rank 1,
- **R2**: rank-1 knowledge can only *generate* rank-1 messages (the
  intruder can never manufacture a secret from safe pieces),
- **R3**: the "bad" events being guarded against are rank 0,
- **R4**: every honest participant's process individually **maintains
  rank** (never emits a rank-0 message having only received rank-1 ones) —

then the protocol satisfies the corresponding `R precedes T` safety
property, *unconditionally* (no assumption about the intruder's number of
reasoning steps, unlike the model-checking result). The chapter's own
closing note: the rank function that proves N-S-L correct provably
*fails* R4 for plain N-S — the message `{Na.Nb}pk(A)` (missing the
responder's identity) is, structurally, already rank 0.

`main.py`'s `rank()` is an original, simplified illustration of this idea
(not a mechanization of R1-R4, which requires a process-level proof
calculus this file doesn't build) — grounded in Example 76.3's own
rationale: participant names/public keys/the intruder's own private key
are rank 1; other private keys and the target secret nonce are rank 0; a
pair is only as safe as its least-safe part; and — the crucial
protective move — the N-S-L-shaped ciphertext `{Na.Nb.B}pk(A)` is
special-cased to rank 1, because even though its *plaintext* contains the
rank-0 secret, only `A` can ever decrypt it, so the ciphertext itself is
safe to circulate. Run against the two concrete messages from Sec. 8.3's
attack: the N-S-L shape gets rank 1 (protected); the N-S shape, lacking
that special case, computes to rank 0 directly — a concrete, checkable
echo of the book's own remark that plain N-S "does not maintain rank."

## 8.7 Closing remarks

Model checking and theorem proving are **complementary**, not competing:
model checking is cheap for finding a counterexample (a broken protocol)
but can time out trying to prove correctness; theorem proving via rank
functions is comparatively easy once you have a valid rank function
(constructing one is the hard, creative part) and proves correctness
unconditionally, but proving *incorrectness* this way would require
showing *no* rank function exists at all — impractical. Rule of thumb:
"the protocol is flawed" → reach for model checking; "the protocol is
correct" → reach for theorem proving.

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
python "Formal Verification of Security Protocols/main.py"
```

## Dependencies

None — everything here uses only the Python standard library.
