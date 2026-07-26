#!/usr/bin/env python3
"""kernel_function_census -- the repo-side, zero-kernel-surface drift backstop ledger row 1433
Tier A commissions (row 1435's build finding, row 1439's merge record): "any delta changing a
[kernel function] body it did not declare surfaces ... before any real world is born." s63
(kernel/lineage/s63-supersession-body-restoration.sql, merged 3bcf1eb) repaired the s61 regression
(row 1430: `validate_supersession_target` silently lost four refusal branches when a re-issue
cited a stale base) but that repair was SQL-side only -- nothing stood between a future re-issue
and the identical mistake, other than gates/lineage_reissue_lineage.py's narrower citation/hash-
binding check on the LINEAGE FILES. This instrument checks the other end of the same class: what
the kernel actually BECOMES once born, not what any lineage file merely claims about itself.

WHAT IT DOES. Births a scratch world through the REAL, FULL --new-world path
(bootstrap/new-project.sh, the identical generator every operator's own world goes through --
never a hand-picked subset of lineage files), interrogates the live catalog for every function
`pg_get_functiondef` can see in that world's two governed schemas (the plain schema and its
paired `_kernel` schema -- together "the kernel" in this project's own vocabulary, see
kernel/lineage/README.md), hashes each function's canonical deployed text, and diffs the result
against gates/kernel_function_census_bank.json -- a committed record this repo carries of what
every kernel function's body sha256 was the last time someone looked and said so. Three drift
shapes, reported distinctly, never collapsed into one bit:

  BODY-CHANGED     -- a function exists in both, but its deployed hash != its banked hash. The
                       s61 hazard, generalized to every function rather than one.
  UNBANKED-FUNCTION -- a function exists live but has no bank entry at all (a NEW function that
                       nobody has yet declared the census owns).
  BANKED-MISSING    -- a function has a bank entry but no longer exists live (dropped, renamed,
                       or a stale entry left behind by drift in the other direction).

ADVISORY POLARITY (explicit, per the commission): this instrument REPORTS. It refuses nothing at
runtime, is not wired into hooks/, and is not invoked by any other gate -- running it is a
standing operator/orchestrator act (`python3 gates/kernel_function_census.py`), same status as
`autoharn doctor`. Wiring it into an enforcement path is the same maintainer session-gap hooks
decision already tracked at ledger row 1438 for gates/lineage_reissue_lineage.py; this file makes
no wiring claim for itself either.

THE BANK. Keyed by "<scope>:<function-name>" where scope is "schema" or "kern" (the two
governed namespaces a --new-world birth creates) -- never the function's ARGUMENT SIGNATURE,
because this codebase's own house idiom never overloads a kernel function name with two live
bodies side by side (gates/lineage_reissue_lineage.py's own THE INVARIANT paragraph states this
explicitly; re-verified empirically here at authoring time -- no (scope, name) pair repeats in a
live census). Value is the sha256 hex digest of the function's `pg_get_functiondef` text, AFTER
the born world's own scratch schema/kern names are substituted back to the stable placeholders
`<SCHEMA>`/`<KERN>` (same normalization idiom as gates/validation_leaf_manifest_gate.py) so the
bank is schema-agnostic and independent of which literal scratch name any given run happens to
pick. Only the hash is banked, never the full function text -- the spec's own words ("a committed
bank file mapping every kernel function name to the sha256 of its DEPLOYED body").

FIRST SNAPSHOT (this build, ledger rows 1433/1435/1439): banked against the post-s63 head
(s20..s63) -- the census's whole point is to fingerprint the REPAIRED bodies, not the pre-s63
defective ones. The build report accompanying this file's first commit states the banked count
and separately witnesses that `validate_supersession_target`'s banked hash corresponds to s63's
restored UNION body (extracted, branches inspected, then hashed -- not assumed).

USAGE:
    python3 gates/kernel_function_census.py                  # verify: scratch birth, diff, teardown
    python3 gates/kernel_function_census.py --bank            # (re-)write the committed bank from a
                                                               # fresh --new-world birth
    python3 gates/kernel_function_census.py --bank-path P     # read/write an ALTERNATE bank file
                                                               # instead of the committed one -- for
                                                               # witnessing (a doctored copy), never
                                                               # for a real verify/bank run
    python3 gates/kernel_function_census.py --keep-scratch    # leave the scratch world standing
                                                               # (debugging only)

Exit codes: 0 clean (or --bank succeeded), 1 drift reported, 2 usage/psql/scaffold error.

Host resolution: HARNESS_PGHOST then EPISTEMIC_PGHOST then this repo's own deployment.json,
via filing/pghost_resolve.py -- never a literal default (the class that module forecloses).

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
BANK_PATH = REPO / "gates" / "kernel_function_census_bank.json"

sys.path.insert(0, str(REPO / "filing"))
import pghost_resolve  # noqa: E402  (filing/pghost_resolve.py -- never a literal host default)

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
PGDB = "toy"

SCOPES = ("schema", "kern")  # the two governed namespaces a --new-world birth creates


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def _psql(sql: str) -> subprocess.CompletedProcess:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tAq", "-c", sql])


def birth_world() -> tuple[str, str, str, Path, Path]:
    """Births a fresh scratch world through the REAL --new-world generator (the full generated
    chain, s15..head -- never a hand-picked CHAIN list). Returns (world, schema, kern, world_dir,
    tmp_root); world == schema (--new-world derives schema/kern/role from the world name).
    Prefixed + random-suffixed so concurrent builders on a shared DB host never collide
    (concurrent-builders-need-isolation)."""
    world = f"kfcensus{secrets.token_hex(4)}"
    tmp_root = Path(tempfile.mkdtemp(prefix=f"{world}-scratch-"))
    world_dir = tmp_root / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        shutil.rmtree(tmp_root, ignore_errors=True)
        raise RuntimeError(f"--new-world birth FAILED for {world!r}:\n{r.stdout[-2500:]}\n{r.stderr[-2500:]}")
    kern = f"{world}_kernel"
    return world, world, kern, world_dir, tmp_root


def teardown(schema: str, kern: str, tmp_root: Path | None, *, show: bool = True) -> str:
    """Drops the scratch world's two schemas + its role, removes the scaffold's own temp
    directory. Returns the psql teardown output (the commission's own "teardown output shown").
    declared-drop: kfcensus-scratch (this function's whole job is the declared teardown of the
    exact schema/kern/role birth_world() just created -- the blast radius is this call's own
    single argument, never wider)."""
    role = f"{schema}_rw"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
             f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "  # declared-drop: kfcensus-scratch
             f"DROP OWNED BY {role};"])
    cp2 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])
    out = (cp.stdout + cp.stderr + cp2.stdout + cp2.stderr).strip()
    if tmp_root is not None:
        shutil.rmtree(tmp_root, ignore_errors=True)
    if show:
        print(f"-- teardown ({schema}/{kern}/{role}) --\n{out}\n-- teardown done --")
    return out


def list_functions(schema: str, kern: str) -> list[tuple[str, str, int]]:
    """[(scope, proname, oid)] for every function in the two governed namespaces, ordered
    deterministically. Uses a plain pipe-delimited query (oid/nspname/proname never contain '|'
    or newlines) -- the full function TEXT is fetched separately, per-oid, exactly like
    gates/validation_leaf_manifest_gate.py's own leaf_functiondef (a multi-line psql -tA value is
    safe only when it is the SOLE column of a SOLE row)."""
    cp = _psql(
        f"SELECT p.oid, n.nspname, p.proname FROM pg_proc p "
        f"JOIN pg_namespace n ON n.oid = p.pronamespace "
        f"WHERE n.nspname IN ('{schema}', '{kern}') "
        f"ORDER BY n.nspname, p.proname, p.oid;")
    if cp.returncode != 0:
        raise RuntimeError(f"list_functions FAILED: {cp.stdout[-1000:]} {cp.stderr[-1000:]}")
    out: list[tuple[str, str, int]] = []
    for line in cp.stdout.splitlines():
        if not line.strip():
            continue
        oid_s, nspname, proname = line.split("|", 2)
        scope = "schema" if nspname == schema else "kern"
        out.append((scope, proname, int(oid_s)))
    return out


def functiondef(oid: int) -> str:
    cp = _psql(f"SELECT pg_get_functiondef({oid});")
    if cp.returncode != 0:
        raise RuntimeError(f"pg_get_functiondef({oid}) FAILED: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def normalize(text: str, schema: str, kern: str) -> str:
    """Schema-agnostic canonical form -- kern first (it contains schema as a strict textual
    prefix, e.g. kfcensusNNNN_kernel contains kfcensusNNNN; word-boundary regex would still be
    safe either order since '_' is a word character and blocks the boundary, but kern-first keeps
    the intent obvious without relying on that subtlety)."""
    text = re.sub(rf"\b{re.escape(kern)}\b", "<KERN>", text)
    text = re.sub(rf"\b{re.escape(schema)}\b", "<SCHEMA>", text)
    return text


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def capture_all(schema: str, kern: str) -> dict[str, str]:
    """{"<scope>:<name>": sha256(normalized canonical text)} for every function live in the two
    governed namespaces. Duplicate (scope, name) pairs would collide here -- checked explicitly
    (never silently overwritten) because this codebase's own house idiom asserts no kernel
    function is ever overloaded (gates/lineage_reissue_lineage.py's THE INVARIANT paragraph)."""
    out: dict[str, str] = {}
    seen: set[str] = set()
    for scope, name, oid in list_functions(schema, kern):
        key = f"{scope}:{name}"
        if key in seen:
            raise RuntimeError(
                f"UNEXPECTED OVERLOAD: {key!r} appears more than once in the live catalog -- "
                f"this codebase's own house idiom (gates/lineage_reissue_lineage.py) asserts no "
                f"kernel function is ever overloaded; this census's key scheme (bare name, no "
                f"signature) assumed that. Investigate before trusting this run's census.")
        seen.add(key)
        text = normalize(functiondef(oid), schema, kern)
        out[key] = digest(text)
    return out


def _no_duplicate_keys(pairs: list[tuple[str, str]]) -> dict[str, str]:
    """object_pairs_hook for json.loads -- json.loads' default dict-building silently keeps only
    the LAST value of a repeated key, so a hand-edited bank with the same function name twice
    would pass with zero warning (the exact hazard a bank diff exists to catch, turned against
    itself). REFUSE loudly instead, naming every duplicated key -- never a silent last-write-wins."""
    seen: dict[str, int] = {}
    for k, _ in pairs:
        seen[k] = seen.get(k, 0) + 1
    dupes = sorted(k for k, n in seen.items() if n > 1)
    if dupes:
        raise SystemExit(
            f"REFUSED: gates/kernel_function_census_bank.json (or the --bank-path given) "
            f"contains {len(dupes)} duplicated key(s), which json.loads would otherwise silently "
            f"resolve to only the LAST occurrence's value -- corrupting the audit value of every "
            f"diff this bank feeds. Duplicated key(s): {', '.join(dupes)}. Fix: remove the "
            f"duplicate entry/entries (or re-run --bank to regenerate the whole file cleanly) "
            f"before trusting any verify/self-test run against this bank.")
    return dict(pairs)


def load_bank(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)


def save_bank(path: Path, bank: dict[str, str]) -> None:
    path.write_text(json.dumps(bank, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def diff_census(live: dict[str, str], banked: dict[str, str]) -> list[str]:
    """Every drift line names the function, both hashes, and the update path -- the commission's
    own teach-first requirement. Three shapes, never collapsed."""
    lines: list[str] = []
    for key in sorted(set(live) | set(banked)):
        lv, bk = live.get(key), banked.get(key)
        if lv == bk:
            continue
        if lv is not None and bk is not None:
            lines.append(
                f"BODY-CHANGED: {key} -- banked sha256={bk} deployed sha256={lv}. If this "
                f"change is deliberate, re-bank in the SAME COMMIT that changes the body -- the "
                f"update IS the declaration (run `python3 gates/kernel_function_census.py --bank` "
                f"and commit the refreshed gates/kernel_function_census_bank.json alongside the "
                f"lineage delta). If it is NOT deliberate, this is the s61-class hazard this "
                f"instrument exists to catch.")
        elif lv is not None:
            lines.append(
                f"UNBANKED-FUNCTION: {key} -- exists in the deployed catalog (sha256={lv}) but "
                f"has no bank entry. Run `python3 gates/kernel_function_census.py --bank` after "
                f"confirming this function's body is the intended, reviewed shape, then commit "
                f"the refreshed bank alongside the delta that introduced it.")
        else:
            lines.append(
                f"BANKED-MISSING: {key} -- has a bank entry (sha256={bk}) but no longer exists "
                f"in the deployed catalog. If the function was deliberately dropped/renamed, "
                f"remove its entry (or run --bank to regenerate the whole bank) in the SAME "
                f"COMMIT that dropped it; otherwise this is an unexplained regression.")
    return lines


def self_test(live: dict[str, str], true_bank: dict[str, str]) -> int:
    """The commission's four-case witness plan (row 1433 item 4), run against ONE real scratch
    birth's live census (efficient -- one world, four assertions on the diffing logic against
    manufactured bank variants; the scratch-DB requirement is satisfied by `live` itself having
    come from a real --new-world birth, teardown happens in the caller). Prints WITNESSED/FAILED
    per case; returns 0 iff all four match the commission's expected shape."""
    fails: list[str] = []
    sample_key = next(iter(sorted(live)))

    # (a) doctored bank entry (wrong hash for one function) -> body-changed naming that function
    doctored = dict(true_bank)
    doctored[sample_key] = "0" * 64
    d = diff_census(live, doctored)
    hit = [l for l in d if l.startswith(f"BODY-CHANGED: {sample_key} ")]
    ok = len(hit) == 1 and all(not l.startswith(("UNBANKED-FUNCTION", "BANKED-MISSING")) or
                                sample_key not in l for l in d)
    print(f"(a) doctored-entry -> BODY-CHANGED naming {sample_key!r}: "
          f"{'WITNESSED' if ok else 'FAILED'}\n    {hit[0] if hit else '(no matching line)'}")
    if not ok:
        fails.append("case (a) doctored bank entry")

    # (b) bank entry for a nonexistent function -> banked-missing
    ghost_key = "schema:not_a_real_kernel_function_xyz"
    doctored_b = dict(true_bank)
    doctored_b[ghost_key] = "f" * 64
    d = diff_census(live, doctored_b)
    hit = [l for l in d if l.startswith(f"BANKED-MISSING: {ghost_key} ")]
    ok = len(hit) == 1
    print(f"(b) nonexistent-function bank entry -> BANKED-MISSING naming {ghost_key!r}: "
          f"{'WITNESSED' if ok else 'FAILED'}\n    {hit[0] if hit else '(no matching line)'}")
    if not ok:
        fails.append("case (b) bank entry for nonexistent function")

    # (c) delete a bank entry -> unbanked-function
    doctored_c = dict(true_bank)
    del doctored_c[sample_key]
    d = diff_census(live, doctored_c)
    hit = [l for l in d if l.startswith(f"UNBANKED-FUNCTION: {sample_key} ")]
    ok = len(hit) == 1
    print(f"(c) deleted bank entry -> UNBANKED-FUNCTION naming {sample_key!r}: "
          f"{'WITNESSED' if ok else 'FAILED'}\n    {hit[0] if hit else '(no matching line)'}")
    if not ok:
        fails.append("case (c) deleted bank entry")

    # (d) clean run against the true bank -> zero drift
    d = diff_census(live, true_bank)
    ok = len(d) == 0
    print(f"(d) clean run against the true bank -> zero drift: "
          f"{'WITNESSED' if ok else 'FAILED'}\n    drift lines: {d if d else '(none)'}")
    if not ok:
        fails.append("case (d) clean run against true bank")

    if fails:
        print(f"\nself-test: {len(fails)}/4 case(s) FAILED: {fails}")
        return 1
    print("\nself-test: 4/4 cases WITNESSED against one real --new-world scratch birth.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", action="store_true",
                     help="birth a fresh --new-world scratch world and (re-)write the bank file")
    ap.add_argument("--bank-path", default=str(BANK_PATH),
                     help="alternate bank file to read/write -- for witnessing a doctored copy; "
                          "never for a real verify/bank run against the committed bank")
    ap.add_argument("--keep-scratch", action="store_true",
                     help="leave the scratch world standing (debugging only)")
    ap.add_argument("--self-test", action="store_true",
                     help="run the four-case witness plan (doctored/nonexistent/deleted/clean "
                          "bank entries) against one real scratch birth's live census, then exit "
                          "-- never mutates the committed bank")
    a = ap.parse_args(argv)
    bank_path = Path(a.bank_path)

    world = schema = kern = None
    world_dir = tmp_root = None
    try:
        world, schema, kern, world_dir, tmp_root = birth_world()
        print(f"-- born: world={world} schema={schema} kern={kern} dest={world_dir} --")
        live = capture_all(schema, kern)
        print(f"-- census: {len(live)} function(s) live in {schema}+{kern} --")

        if a.self_test:
            return self_test(live, load_bank(bank_path))

        if a.bank:
            save_bank(bank_path, live)
            print(f"kernel-function-census: BANKED {len(live)} function(s) to "
                  f"{bank_path if bank_path != BANK_PATH else bank_path.relative_to(REPO)}")
            return 0

        banked = load_bank(bank_path)
        drift = diff_census(live, banked)
    except RuntimeError as exc:
        print(f"kernel-function-census: SCRATCH BIRTH/CENSUS ERROR -- {exc}")
        return 2
    finally:
        if world is not None:
            if a.keep_scratch:
                print(f"kernel-function-census: --keep-scratch -- {schema}/{kern}/{schema}_rw "
                      f"left standing, {world_dir} left on disk")
            else:
                teardown(schema, kern, tmp_root)

    if drift:
        print(f"kernel-function-census: {len(drift)} drift line(s) (ADVISORY -- reports only, "
              f"refuses nothing, not wired into hooks/):\n")
        for line in drift:
            print(f"  !! {line}\n")
        return 1
    print(f"kernel-function-census: clean -- {len(live)} function(s) match the banked census "
          f"exactly. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
