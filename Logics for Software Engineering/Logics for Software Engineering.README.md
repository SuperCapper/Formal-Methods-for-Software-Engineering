# Logics for Software Engineering

Companion notes/code for the "Logics" module of the *Formal Methods for
Software Engineering* coursework (see the top-level [README.md](../README.md)
for the course as a whole).

## Status

`main.py` is currently an empty stub — no code has been written yet. This
README will be filled in as the module grows.

Planned scope (typical for this topic in a formal methods course):
- Propositional logic (syntax, semantics, satisfiability)
- Predicate / first-order logic
- Temporal logic (LTL/CTL) as used in model checking

## Environment

A local virtual environment lives at the repo root in `.venv/` (Python
3.14, stdlib only — no third-party packages installed yet). Activate it
from the repo root:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Git Bash
source .venv/Scripts/activate
```

Run the module (from the repo root):

```bash
python "Logics for Software Engineering/main.py"
```

## Dependencies

None yet. If the module grows to need packages (e.g. `sympy` for symbolic
logic), record them in a `requirements.txt` in this folder.
