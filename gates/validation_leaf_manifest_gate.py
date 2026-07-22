#!/usr/bin/env python3
"""validation_leaf_manifest_gate -- the BYTE-IDENTITY mechanism F4's own real hazard names
(vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F4 / plan step 7; design/
ORCH-IDRIS-REFINEMENT-CONSULT-2026-07-15.md R8's "typed premise list is the natural manifest
source" lowering row; ledger item validation-trigger-decomposition).

WHAT THIS IS. kernel/lineage/s22-work-item-ledger.sql defined validate_work_item(); s28, s29
(twice), s30, s31, s33 each RE-ISSUED the whole function, copying every prior branch forward with
only a PROSE assertion of byte-identity ("s30 (unchanged, byte-for-byte)"). That prose is
checkable by no mechanism -- a silent one-character mutation in a re-issue would ship undetected.
s35 (kernel/lineage/s35-validation-decomposition.sql) breaks the monolith into a thin dispatcher
plus four per-concern LEAF functions (validate_work_item_open, validate_work_item_depends,
validate_work_item_close_is_composite, validate_work_item_close) precisely so a FUTURE delta can
re-issue ONE leaf without touching the other three -- but "re-issue ONE leaf, unchanged" is
exactly as prose-only a claim as s28..s33's own "unchanged, byte-for-byte" comments were, unless
something checks it. This gate is that something: a DECLARED-CHANGE MANIFEST (the refinement
consult's own name for the idea) banking the canonical text of every leaf, refusing a re-issue
that silently changes a leaf's canonical text without --declare-change naming it.

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: for every leaf function in LEAVES below, the live catalog's canonical text
    (pg_get_functiondef, with the scratch schema's own name normalized to the placeholder
    <SCHEMA> so the banked manifest is schema-agnostic) equals the BANKED canonical text in
    gates/validation_leaf_manifest.json, UNLESS the leaf's name appears in --declare-change.
  - QUANTIFICATION UNIVERSE: the four leaves s35 mints (LEAVES below) -- not the dispatcher
    itself (validate_work_item() is EXPECTED to change shape as future kind-routing evolves; its
    own byte-identity is s35's .detect sibling's concern, not this gate's) and not
    validate_independence() (s34's disjoint territory, untouched by s35, out of this gate's
    scope by construction -- adding it is a future delta's own manifest entry, not a retrofit
    here). A leaf function ABSENT from the live catalog (e.g. a pre-s35 kernel) is reported
    distinctly from a leaf whose text DIFFERS from the manifest.
  - DENOMINATION: one violation per (leaf, mismatch-kind) -- absent, or a text diff naming the
    leaf and showing the unified diff between banked and live canonical text. Never a single
    pass/fail bit with no detail.

MODE: a live-Postgres, scratch-apply gate (kind_shape_manifest_gate.py's own idiom, not the
file-scanning gates/doc_tables.py idiom) -- applies the full birth chain through s35 (skipping
s34, a disjoint concurrent delta this gate's own chain does not depend on) to a throwaway schema,
interrogates the catalog, tears down.

USAGE:
    python3 gates/validation_leaf_manifest_gate.py                      # verify, scratch apply+teardown
    python3 gates/validation_leaf_manifest_gate.py --bank                # (re-)bank the manifest from the live chain
    python3 gates/validation_leaf_manifest_gate.py --red                 # seen-red: mutate one leaf UNDECLARED, expect refusal
    python3 gates/validation_leaf_manifest_gate.py --declare-change validate_work_item_open
    python3 gates/validation_leaf_manifest_gate.py --keep-scratch

Exit codes: 0 clean, 1 violations (listed), 2 usage/psql/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINEAGE = REPO / "kernel" / "lineage"
MANIFEST_PATH = REPO / "gates" / "validation_leaf_manifest.json"

PGHOST = "192.168.122.1"
PGDB = "toy"

# Full birth chain through s35 -- s34 (validate_independence(), a concurrent, disjoint delta) is
# deliberately EXCLUDED: s35's own leaves make no reference to it, and this gate's own commission
# forbids depending on s34 objects.
CHAIN = [
    "high_watermark_1.sql",
    "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql",
    "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql",
    "s24-declared-event-time.sql",
    "s25-commission-kind.sql",
    "s26-row-hash-chain.sql",
    "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql",
    "s33-composite-discharge.sql",
    "s35-validation-decomposition.sql",
]

# LEAVES: {leaf_name: (arg_types_for_to_regprocedure_lookup,)} -- arg types spelled with the
# <SCHEMA> placeholder for the one composite type argument (ledger), substituted with the live
# scratch schema name at lookup time.
LEAVES = {
    "validate_work_item_open": ("<SCHEMA>.ledger",),
    "validate_work_item_depends": ("<SCHEMA>.ledger",),
    "validate_work_item_close_is_composite": ("text",),
    "validate_work_item_close": ("<SCHEMA>.ledger", "boolean", "text"),
}


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def _psql(sql: str) -> subprocess.CompletedProcess:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tAq", "-c", sql])


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
        f"DROP OWNED BY {role};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def leaf_functiondef(schema: str, name: str, arg_types: tuple[str, ...]) -> str | None:
    """Live canonical text (pg_get_functiondef) of one leaf, or None if it does not exist on
    this schema (pre-s35 kernel, or a --red run that dropped it)."""
    sig = ", ".join(t.replace("<SCHEMA>", schema) for t in arg_types)
    cp = _psql(f"SELECT pg_get_functiondef('{schema}.{name}({sig})'::regprocedure);")
    if cp.returncode != 0:
        return None
    text = cp.stdout.strip()
    return text or None


def normalize(text: str, schema: str) -> str:
    """Schema-agnostic canonical form -- replace every occurrence of the live scratch schema
    name with the <SCHEMA> placeholder, so the banked manifest never encodes a scratch-run-
    specific schema name."""
    return re.sub(rf"\b{re.escape(schema)}\b", "<SCHEMA>", text)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture_all(schema: str) -> dict[str, str]:
    """{leaf_name: normalized canonical text} for every leaf in LEAVES, live on `schema`."""
    out: dict[str, str] = {}
    for name, arg_types in LEAVES.items():
        text = leaf_functiondef(schema, name, arg_types)
        if text is not None:
            out[name] = normalize(text, schema)
    return out


def load_manifest() -> dict[str, str]:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, str]) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_manifest(live: dict[str, str], banked: dict[str, str],
                     declared_change: set[str]) -> list[str]:
    violations: list[str] = []
    for name in LEAVES:
        if name not in live:
            violations.append(
                f"LEAF ABSENT: {name!r} is declared in LEAVES but does not exist in the live "
                f"catalog -- pre-s35 kernel, or a dropped leaf.")
            continue
        if name not in banked:
            violations.append(
                f"UNBANKED LEAF: {name!r} exists live but has no manifest entry -- run "
                f"--bank after confirming its canonical text is the intended, reviewed shape.")
            continue
        if live[name] == banked[name]:
            continue
        if name in declared_change:
            continue  # a legitimate, --declare-change'd re-issue -- not a violation
        diff = "\n".join(difflib.unified_diff(
            banked[name].splitlines(), live[name].splitlines(),
            fromfile=f"banked/{name}", tofile=f"live/{name}", lineterm=""))
        violations.append(
            f"UNDECLARED LEAF MUTATION: {name!r}'s live canonical text differs from the banked "
            f"manifest, and {name!r} was not named in --declare-change. This is EXACTLY the "
            f"hazard s28..s33's own 'unchanged, byte-for-byte' prose comments could never check "
            f"(F4). If this change is deliberate, re-run with --declare-change {name}, review "
            f"the diff below, then --bank to update the manifest.\n{diff}")
    for name in banked:
        if name not in LEAVES:
            violations.append(
                f"STALE MANIFEST ENTRY: {name!r} is banked but not declared in LEAVES -- "
                f"MANIFEST/LEAVES drifted; remove the entry or add it to LEAVES.")
    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-scratch", action="store_true")
    ap.add_argument("--bank", action="store_true",
                     help="apply the real chain and (re-)write gates/validation_leaf_manifest.json")
    ap.add_argument("--red", action="store_true",
                     help="seen-red negative control: after the real chain applies, mutate ONE "
                          "leaf's body (CREATE OR REPLACE, undeclared) and confirm this gate "
                          "REFUSES it")
    ap.add_argument("--declare-change", default="",
                     help="comma-separated leaf names whose text mismatch is expected (a "
                          "legitimate, reviewed re-issue) -- suppresses the violation for those "
                          "leaves only")
    a = ap.parse_args(argv)
    declared = {s.strip() for s in a.declare_change.split(",") if s.strip()}

    suffix = "vlmg_scratch"
    schema, kern, role = suffix, f"{suffix}_kernel", f"{suffix}_rw"
    teardown(schema, kern, role)
    try:
        apply_chain(schema, kern, role)
        if a.red:
            # Deliberately misfactor ONE leaf -- an undeclared, silent text mutation, the exact
            # shape s28..s33's prose-only "byte-identical" claims could never catch.
            cp = _psql(
                f"CREATE OR REPLACE FUNCTION {schema}.validate_work_item_close_is_composite"
                f"(p_work_slug text) RETURNS boolean LANGUAGE plpgsql "
                f"SET search_path = {schema}, {kern}, pg_temp AS $fn$ "
                f"BEGIN RETURN false; END; $fn$;")
            if cp.returncode != 0:
                print(f"validation-leaf-manifest-gate: --red mutation FAILED: {cp.stderr}")
                return 2
        if a.bank:
            manifest = capture_all(schema)
            save_manifest(manifest)
            print(f"validation-leaf-manifest-gate: BANKED {len(manifest)} leaf(ves) to "
                  f"{MANIFEST_PATH.relative_to(REPO)}")
            return 0
        live = capture_all(schema)
        banked = load_manifest()
        violations = assert_manifest(live, banked, declared)
    except RuntimeError as exc:
        print(f"validation-leaf-manifest-gate: SCRATCH APPLY ERROR -- {exc}")
        return 2
    finally:
        if not a.keep_scratch:
            teardown(schema, kern, role)
        else:
            print(f"validation-leaf-manifest-gate: --keep-scratch -- schema={schema} left standing")

    if violations:
        print(f"validation-leaf-manifest-gate: {len(violations)} violation(s):\n")
        for v in violations:
            print(f"  !! {v}\n")
        return 1
    print(f"validation-leaf-manifest-gate: clean -- {len(LEAVES)} leaf(ves) match the banked "
          f"manifest exactly{' (' + str(len(declared)) + ' declared change(s) exempted)' if declared else ''}. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
