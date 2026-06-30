#!/usr/bin/env python
"""ASP logic-layer driver -- the paraconsistent, differential-gated logic layer over
the Python contradiction oracle (contra_detect.find_contradictions), via the clingo
CLI as a subprocess (the Python `clingo` binding is NOT in the venv -- B-autoharn-fit
s.0: "subprocess-from-Python today").

It is ADDITIVE and REVERSIBLE: contra_detect.py and schema.sql are UNCHANGED. The
ASP program (logic_layer.lp) re-expresses the SAME three rules over an EDB exported
from the SAME Claims the Python detector reads, so the two can be DIFFERENTIALLY
GATED -- any divergence is an encoding bug surfaced BEFORE trust (ADR-0000/INDEP;
ADR-0002 fail-loud). The honesty posture of contra_detect carries over: no score, no
guess; the parse is done once in Python and the canonical value shipped as a term.

Shared identity: a Claim's index in claims_from_bundle(bundle) is its ASP `Id`. The
ASP side emits findings as integer-id pairs only (no text crosses the wire); the
differential maps both sides into ONE signature -- (rule, subj_key, pred, sorted pair
of _claim_text) -- exactly the key find_contradictions() dedups on. So neither side
re-derives the other's claim text; clingo decides WHICH pairs are findings (the
logic), Python supplies the surfaces (the data).

CLI:
    python contra_asp.py --synthetic                 # ASP findings on the planted fixture
    python contra_asp.py --differential --synthetic  # ASP vs Python oracle, must MATCH
    python contra_asp.py --differential --rfc PATH    # the same gate on a real doc
    python contra_asp.py --repair --synthetic         # minimal-repair / blame (ASP>SQL)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import contra_detect as cd
import extract
from logic_backend import LogicFinding

HERE = Path(__file__).resolve().parent
LOGIC_LP = HERE / "logic_layer.lp"
REPAIR_LP = HERE / "logic_repair.lp"

# the rule-tag the .lp emits (a bare clingo constant) -> the canonical rule id.
_TAG_TO_RULE = {"neg": "R-NEG", "func": "R-FUNC", "num": "R-NUM"}


# ----------------------------------------------------------------- EDB export --
def _quote(s: str) -> str:
    r"""A clingo double-quoted string term, escaping the only two metacharacters
    (\ and ") so any canonical key/lemma is a legal term regardless of content."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _canon_number(n: float) -> str:
    """Canonical string for a parsed numeric value. repr(float) is stable and
    collision-free over equality (repr(3.0)=='3.0'==repr(3.0)), so two claims whose
    objects parse to the SAME number ship the SAME term -> no spurious R-NUM, exactly
    as the Python rule (a.number != b.number) intends."""
    return repr(n)


def edb_from_claims(
    claims: list[cd.Claim],
    functional_preds: Iterable[str] = cd.FUNCTIONAL_PREDS,
    extra_facts: str = "",
) -> str:
    """Render the shared EDB as clingo facts from the SAME claims the Python oracle
    consumes. `functional_preds` becomes `functional/1` DATA (the FUNCTIONAL_PREDS
    frozenset moved OUT of code into an auditable, retractable fact -- the research
    calls for exactly this). `extra_facts` injects further EDB (e.g. multi_valued/2
    defeaters) without touching the program."""
    lines: list[str] = ["% --- EDB (generated from contra_detect.Claim list) ---"]
    for pred in sorted(set(functional_preds)):
        lines.append(f"functional({_quote(pred)}).")
    for i, c in enumerate(claims):
        pol = "neg" if c.negated else "pos"
        lines.append(
            f"assertion({i},{_quote(c.subj_key)},{_quote(c.pred)},"
            f"{_quote(c.obj_key)},{pol})."
        )
        if c.number is not None:
            lines.append(f"number({i},{_quote(_canon_number(c.number))}).")
    if extra_facts.strip():
        lines.append("% --- injected extra EDB ---")
        lines.append(extra_facts.strip())
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------- clingo runner --
def _clingo_bin() -> str:
    exe = shutil.which("clingo")
    if exe is None:  # ADR-0002: fail loud, never silently no-op
        raise RuntimeError("clingo CLI not found on PATH (need clingo 5.8.x)")
    return exe


def run_clingo(program_files: list[Path], edb_text: str, opt: bool = False) -> list[str]:
    """Run clingo over `program_files` + the EDB (fed on stdin) and return the shown
    atoms of the relevant model as strings. For the detector the program is stratified
    (exactly one stable model -> Witnesses[0]); for the optimisation (`opt=True`) the
    OPTIMUM is the LAST witness clingo reports. JSON output (`--outf=2`) is parsed --
    no brittle text scraping."""
    cmd = [_clingo_bin(), *[str(p) for p in program_files], "-", "--outf=2"]
    if opt:
        # enumerate to the optimum; clingo prints improving models, last is optimal.
        cmd += ["--opt-mode=opt"]
    proc = subprocess.run(
        cmd, input=edb_text, capture_output=True, text=True, timeout=120
    )
    # clingo exit codes are a bitmask (10=SAT, 20=UNSAT, 30=SAT+INTERRUPT...); a
    # non-zero code is NORMAL. A parse/grounding error prints to stderr with code 1/65.
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as e:  # ADR-0002: surface the real clingo error
        raise RuntimeError(
            f"clingo produced no JSON (exit {proc.returncode}): {proc.stderr.strip()}"
        ) from e
    result = out.get("Result", "")
    if result == "UNSATISFIABLE":
        return []
    calls = out.get("Call", [])
    if not calls:
        return []
    witnesses = calls[-1].get("Witnesses", [])
    if not witnesses:
        return []
    return list(witnesses[-1].get("Value", []))


# ----------------------------------------------------------------- findings ----
@dataclass(frozen=True)
class AspFinding:
    """An ASP-derived finding, mapped back to the two source Claims by id."""

    rule: str          # R-NEG | R-FUNC | R-NUM
    a: cd.Claim
    b: cd.Claim

    @property
    def signature(self) -> tuple[str, str, str, tuple[str, str]]:
        return _signature(self.rule, self.a, self.b)


def _signature(rule: str, a: cd.Claim, b: cd.Claim) -> tuple[str, str, str, tuple[str, str]]:
    """The ONE comparison key both sides land in: (rule, subj_key, pred, sorted pair
    of the human-readable claim text). It is exactly the tuple find_contradictions()
    dedups on (rule, subj_key, pred, claim_a, claim_b), made order-insensitive by
    sorting -- so A/B ordering and the reverse-pair dedup cannot cause a false
    divergence. _claim_text is reused verbatim, so the text is identical by
    construction; the ONLY thing under test is which PAIRS each side finds."""
    texts = tuple(sorted((cd._claim_text(a), cd._claim_text(b))))
    return (rule, a.subj_key, a.pred, texts)  # subj_key/pred shared by both claims


def _parse_finding_atoms(atoms: list[str]) -> list[tuple[str, int, int]]:
    """Pull (tag, id_a, id_b) out of the `finding(tag,A,B)` atoms. Tag is a bare
    constant and A,B are integers -- no string parsing, so claim text never has to be
    recovered from clingo output."""
    out: list[tuple[str, int, int]] = []
    for atom in atoms:
        if not atom.startswith("finding("):
            continue
        inner = atom[len("finding("):-1]  # strip 'finding(' .. ')'
        tag, sa, sb = (p.strip() for p in inner.split(","))
        out.append((tag, int(sa), int(sb)))
    return out


def asp_findings(
    claims: list[cd.Claim],
    functional_preds: Iterable[str] = cd.FUNCTIONAL_PREDS,
    extra_facts: str = "",
) -> list[AspFinding]:
    """Run logic_layer.lp on the claims and return the ASP findings, mapped to Claims."""
    edb = edb_from_claims(claims, functional_preds, extra_facts)
    atoms = run_clingo([LOGIC_LP], edb)
    findings: list[AspFinding] = []
    for tag, ia, ib in _parse_finding_atoms(atoms):
        findings.append(AspFinding(_TAG_TO_RULE[tag], claims[ia], claims[ib]))
    return findings


def asp_signatures(claims: list[cd.Claim], **kw) -> set:
    return {f.signature for f in asp_findings(claims, **kw)}


def py_signatures(claims: list[cd.Claim], **kw) -> set:
    """The Python oracle's findings, in the SAME signature space."""
    return {
        (f.rule, f.subj_key, f.pred, tuple(sorted((f.claim_a, f.claim_b))))
        for f in cd.find_contradictions(claims, **kw)
    }


def differential(claims: list[cd.Claim], **kw) -> tuple[set, set]:
    """Return (only_in_asp, only_in_python). EMPTY-EMPTY == the gate passes: clingo
    matches the oracle exactly. Anything else is an encoding bug (ADR-0000 s.5)."""
    a, p = asp_signatures(claims, **kw), py_signatures(claims, **kw)
    return (a - p, p - a)


# ---------------------------------------------------- minimal repair / blame --
def minimal_repair(
    claims: list[cd.Claim],
    functional_preds: Iterable[str] = cd.FUNCTIONAL_PREDS,
    extra_facts: str = "",
) -> list[int]:
    """A minimum-cardinality set of assertion ids whose retraction removes every
    functional conflict (logic_repair.lp). This is the ASP>SQL demonstration:
    subset-optimization a SQL view cannot rank. Returns the claim ids to retract."""
    edb = edb_from_claims(claims, functional_preds, extra_facts)
    atoms = run_clingo([LOGIC_LP, REPAIR_LP], edb, opt=True)
    ids: list[int] = []
    for atom in atoms:
        if atom.startswith("retract("):
            ids.append(int(atom[len("retract("):-1]))
    return sorted(ids)


# --------------------------------------------------- the LogicBackend adapter --
class AspBackend:
    """The FIRST adapter on the standardized `logic_backend.LogicBackend` seam: the
    clingo/ASP engine, plugged onto the `Claim` NLP substrate. It is a THIN wrapper --
    all the encoding (`logic_layer.lp`), the EDB export, and the clingo subprocess
    driver are the existing, differential-gated `contra_asp` functions, UNCHANGED; this
    class only re-shapes `asp_findings` into the engine-neutral `LogicFinding`.

    It covers ALL THREE rules. The defeasible-R-FUNC and numeric knobs the ASP engine
    owns (the `functional/1` allowlist-as-data, the `multi_valued/2` defeater seam) are
    CONSTRUCTOR state here -- engine-specific configuration deliberately kept off the
    standardized Protocol, exactly as impedance keeps a library's capability surface off
    `LibAdapter`. Conforms to `LogicBackend` structurally (by shape, not inheritance)."""

    name = "asp-clingo"
    rules = frozenset({"R-NEG", "R-FUNC", "R-NUM"})

    def __init__(
        self,
        functional_preds: Iterable[str] = cd.FUNCTIONAL_PREDS,
        extra_facts: str = "",
    ) -> None:
        self.functional_preds = functional_preds
        self.extra_facts = extra_facts

    def analyze(self, claims: list[cd.Claim]) -> list[LogicFinding]:
        out: list[LogicFinding] = []
        for f in asp_findings(claims, self.functional_preds, self.extra_facts):
            # R-NEG is the FDE/LP glut -- expose the contained value on the seam so a
            # downstream consumer sees `both`, not an explosion. R-FUNC/R-NUM are
            # classical disequality findings (no derived many-valued value).
            value = "both" if f.rule == "R-NEG" else None
            out.append(LogicFinding.from_claims(f.rule, f.a, f.b, value=value, backend=self.name))
        return out


# ------------------------------------------------------------- claim helpers --
def claims_from_text(text: str, model: str = "en_core_web_sm") -> list[cd.Claim]:
    nlp = extract.load_model(model)
    return cd.claims_from_bundle(extract.doc_to_facts(nlp(text)))


def claims_from_paragraphs(paragraphs: list[str], model: str = "en_core_web_sm") -> list[cd.Claim]:
    nlp = extract.load_model(model)
    claims: list[cd.Claim] = []
    for doc in nlp.pipe(paragraphs):  # type: ignore[attr-defined]
        claims.extend(cd.claims_from_bundle(extract.doc_to_facts(doc)))
    return claims


# ---------------------------------------------------------------------- CLI ---
def _print_findings(findings: list[AspFinding]) -> None:
    if not findings:
        print("  (no findings)")
        return
    for f in findings:
        print(f"  [{f.rule}] subject={f.a.subj_key!r} predicate={f.a.pred!r}")
        print(f"      A: {cd._claim_text(f.a)}")
        print(f"      B: {cd._claim_text(f.b)}")


def _print_differential(only_asp: set, only_py: set) -> bool:
    if not only_asp and not only_py:
        print("  DIFFERENTIAL GATE: PASS -- clingo matches find_contradictions() exactly.")
        return True
    print("  DIFFERENTIAL GATE: FAIL -- encoding bug surfaced before trust (ADR-0000).")
    for s in sorted(map(str, only_asp)):
        print(f"    only in ASP   : {s}")
    for s in sorted(map(str, only_py)):
        print(f"    only in Python: {s}")
    return False


def _load_claims(args) -> tuple[str, list[cd.Claim]]:
    if args.rfc:
        body = extract.normalise(extract.load_body(args.rfc, None))
        paras = [p.strip() for p in body.split("\n\n") if p.strip()][: args.max_paras]
        return f"rfc:{Path(args.rfc).name}", claims_from_paragraphs(paras)
    fixture = HERE / "fixtures" / "contra_synthetic.txt"
    return "synthetic", claims_from_text(fixture.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synthetic", action="store_true", help="the planted fixture (default)")
    ap.add_argument("--rfc", metavar="PATH", default=None, help="a real ~/distill RFC doc")
    ap.add_argument("--max-paras", type=int, default=200, help="paragraph cap for --rfc")
    ap.add_argument("--differential", action="store_true", help="ASP vs Python oracle (must match)")
    ap.add_argument("--repair", action="store_true", help="minimal-repair / blame (ASP>SQL)")
    args = ap.parse_args()

    source, claims = _load_claims(args)
    print(f"=== source: {source} | claims: {len(claims)} ===")

    if args.differential:
        only_asp, only_py = differential(claims)
        ok = _print_differential(only_asp, only_py)
        return 0 if ok else 1

    if args.repair:
        ids = minimal_repair(claims)
        print(f"  minimal functional-conflict repair: retract claim ids {ids}")
        for i in ids:
            print(f"    retract[{i}]: {cd._claim_text(claims[i])}")
        return 0

    findings = asp_findings(claims)
    print(f"  ASP findings: {len(findings)}")
    _print_findings(findings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
