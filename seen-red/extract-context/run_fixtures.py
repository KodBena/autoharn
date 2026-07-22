#!/usr/bin/env python3
"""run_fixtures — both-polarity live proof for extract-context (bootstrap/extract_context.py +
the repo-root `./extract-context` shim; gates/fixture_census.py REGISTRY entry
"extract-context"). Mirrors seen-red/track-work/run_fixtures.py's own scratch-and-drop pattern: a
throwaway SOURCE world and a throwaway TARGET world, both in the TOY db, torn down after unless a
case fails (left standing as evidence).

CASES (both polarities, all live subprocess runs of the real tool -- never a mock):

  GREEN-EXTRACT-DETERMINISTIC -- a fresh `./extract-context extract` against a source world with
                        known, planted content produces a manifest whose item lines (excluding the
                        provenance line's own timestamp) are byte-identical across two independent
                        runs -- extraction is a pure read, not seeded by wall-clock or ordering.

  RED-INGEST-UNREVIEWED -- `./extract-context ingest` against the SAME manifest, before any
                        review marker is appended, is REFUSED WHOLESALE (exit 1) and the target
                        world's ledger row count is provably unchanged (verified by direct SELECT,
                        not by trusting the tool's own exit code alone).

  GREEN-INGEST-ATTRIBUTED -- after a `{"record":"review","reviewed":true,...}` line is appended,
                        the SAME manifest ingests into the (distinct) target world: every carried
                        row lands with `actor` resolving to the EXACT `--actor` name passed on the
                        command line (the row-1943 mechanical check this fixture exists to bank),
                        never the ambient/default connection principal.

  NEGATIVE-CONTROL-NEVER-ABSENT -- planted NEVER-class specimens (a commission row, a snag row,
                        and a write_refused row) each carry a unique marker string in their
                        statement/rationale text. None of those marker strings appears ANYWHERE in
                        the manifest file, byte for byte -- "provably absent," not "believed
                        absent." Grep-checked directly against the manifest file, not against this
                        tool's own self-report.

  DROP-NEVER-SILENT   -- every planted NEVER-class and drop-with-reason specimen (commission, snag,
                        write_refused, review) still appears as its OWN manifest line with
                        disposition "never-class"/"drop-with-reason" and a `reason` string -- i.e.
                        excluded from CONTENT but never excluded from the MANIFEST'S OWN INVENTORY
                        (the distinction the module docstring's "PAYLOAD-FREE CLASSES" section
                        draws, checked here as a live property rather than asserted).

  PRE-S36-FALLBACK    -- row 1950's own live finding (this repo's autoharn1 world predates s36):
                        with the source world's `standing_decisions` VIEW dropped (simulating a
                        pre-s36 kernel without birthing a whole second lineage chain), a fresh
                        extract still carries every unsuperseded kind=decision row from
                        `ledger_current` (s31 semantics) as a 1.2_standing_decisions carry-verbatim
                        item, grade honestly `None` (no grade concept exists pre-s36 -- never
                        invented), plus exactly one class-summary line naming the widening (this
                        fallback carries ALL decision rows, not only the s36 path's graded
                        subset). Run AFTER the other cases above (which need the real
                        standing_decisions view) and last, since dropping the view is irreversible
                        for the remainder of this source world's lifetime in this run.

Scratch-only: two throwaway schema/kern/role triples in the TOY db (192.168.122.1), both dropped
after, UNLESS a case FAILS (left standing as evidence).

Usage: python3 seen-red/extract-context/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
EXTRACT_CONTEXT = REPO / "extract-context"
PGHOST = fixture_pghost()
DB = "toy"

SRC_NAME, TGT_NAME = "ecfxsrcfixture_scratch", "ecfxtgtfixture_scratch"

SECRET_SNAG = "SECRET_MARKER_SNAG_9f3a_fixture"
SECRET_COMMISH = "SECRET_MARKER_COMMISH_1a2b_fixture"
SECRET_REVIEW = "SECRET_MARKER_REVIEW_ab12_fixture"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                          capture_output=True, text=True)


def _drop_scratch(name: str) -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {name} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {name}_kernel CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {name}_rw;")


def _ledger_count(schema: str) -> int:
    r = _psql("-tAc", f"SELECT count(*) FROM {schema}.ledger;")
    return int(r.stdout.strip())


def _birth(dest: Path, world: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(NEW_PROJECT), str(dest), "--new-world", world, "--db", DB, "--host", PGHOST,
         "--name", world],
        capture_output=True, text=True, cwd=str(REPO), timeout=300)


def _led(dest: Path, *args: str, actor: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if actor:
        env["LED_ACTOR"] = actor
    return subprocess.run([str(dest / "legacy" / "led"), *args],
                          capture_output=True, text=True, cwd=str(dest), env=env)


def _extract(deployment: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(EXTRACT_CONTEXT), "extract", "--deployment", str(deployment),
                           "--out", str(out), "--principal", "fixture-extractor"],
                          capture_output=True, text=True, cwd=str(REPO))


def _ingest(manifest: Path, deployment: Path, actor: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(EXTRACT_CONTEXT), "ingest", "--manifest", str(manifest),
                           "--deployment", str(deployment), "--actor", actor],
                          capture_output=True, text=True, cwd=str(REPO))


def _manifest_lines_no_prov_ts(path: Path) -> list[str]:
    """Every manifest line, but the provenance line's own volatile fields (timestamp always
    differs run to run; verify_chain_output embeds a live head hash that also differs once any
    write has happened between runs) are stripped before comparison -- GREEN-EXTRACT-DETERMINISTIC
    is about the tool's OWN read+classify pass being pure, not about the source world being frozen
    in time across two invocations of psql."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        obj = json.loads(line)
        if obj.get("record") == "provenance":
            obj.pop("timestamp", None)
            obj.pop("verify_chain_output", None)
        out.append(json.dumps(obj, sort_keys=True))
    return out


def main() -> int:
    failures: list[str] = []
    _drop_scratch(SRC_NAME)
    _drop_scratch(TGT_NAME)
    tmpdir = Path(tempfile.mkdtemp(prefix="extract-context-fixture-"))
    src_dir, tgt_dir = tmpdir / "src", tmpdir / "tgt"

    # ---------------------------------------------------------------------------- birth both worlds
    r = _birth(src_dir, SRC_NAME)
    if r.returncode != 0:
        print(f"SETUP: source world birth failed, exit={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        return 1
    r = _birth(tgt_dir, TGT_NAME)
    if r.returncode != 0:
        print(f"SETUP: target world birth failed, exit={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        return 1
    print("SETUP: both scratch worlds born -- PASS")

    # ---------------------------------------------------------------------------- seed known content
    _led(src_dir, "decision", "--grade", "durable", "Standing rule ALPHA: fixture-seeded durable decision.")
    _led(src_dir, "decision", "ordinary undurable decision, not standing")
    _led(src_dir, "register-principal", "item-countersign", "subagent", "--purpose", "countersigns items",
        actor="reviewer")
    _led(src_dir, "question", "Is the sky blue in this scratch world?")
    _led(src_dir, "work", "open", "smoke-item", "fixture smoke work item")
    _led(src_dir, "snag", f"{SECRET_SNAG}: plaintext-looking secret, must never leak into a manifest")
    _led(src_dir, "commission", f"{SECRET_COMMISH}: the founding ask, must never leak")
    # a real write_refused specimen: a review claiming non-self-review independence with no
    # stamped invocation to back it -- the kernel's own s43 boundary journals this as a
    # write_refused row (see MAINT-EXPERIENCE-REBIRTH-RUNBOOK.md's own live specimen of this).
    _led(src_dir, "review", "7", "attest", "technical", f"{SECRET_REVIEW}: refused review text",
        actor="reviewer")
    # a review that DOES succeed (self-review, no stamp required) -- a track-record specimen.
    _led(src_dir, "review", "7", "attest", "self-review", f"{SECRET_REVIEW}: self-review text",
        actor="reviewer")

    # ------------------------------------------------------------ GREEN-EXTRACT-DETERMINISTIC (i)
    src_dep = src_dir / "deployment.json"
    manifest1, manifest2 = tmpdir / "m1.jsonl", tmpdir / "m2.jsonl"
    r1 = _extract(src_dep, manifest1)
    r2 = _extract(src_dep, manifest2)
    det_ok = (r1.returncode == 0 and r2.returncode == 0
              and _manifest_lines_no_prov_ts(manifest1) == _manifest_lines_no_prov_ts(manifest2))
    if not det_ok:
        failures.append(f"GREEN-EXTRACT-DETERMINISTIC: two extract runs diverged or failed\n"
                        f"r1={r1.returncode} r2={r2.returncode}\n{r1.stderr}\n{r2.stderr}")
    print(f"GREEN-EXTRACT-DETERMINISTIC: two independent extracts, item lines identical -- "
          f"{'PASS' if det_ok else 'FAIL'}")

    manifest = manifest1
    items = [json.loads(l) for l in manifest.read_text(encoding="utf-8").splitlines()]

    # -------------------------------------------------------------- NEGATIVE-CONTROL (iv)
    raw_text = manifest.read_text(encoding="utf-8")
    leaked = [s for s in (SECRET_SNAG, SECRET_COMMISH, SECRET_REVIEW) if s in raw_text]
    neg_ok = not leaked
    if not neg_ok:
        failures.append(f"NEGATIVE-CONTROL-NEVER-ABSENT: planted secret(s) leaked into manifest: {leaked}")
    print(f"NEGATIVE-CONTROL-NEVER-ABSENT: planted NEVER-class secrets absent from manifest text -- "
          f"{'PASS' if neg_ok else 'FAIL'}")

    # -------------------------------------------------------------- DROP-NEVER-SILENT (v)
    def _has(cls: str, disp: str) -> bool:
        return any(it.get("record") == "item" and it.get("class") == cls and it.get("disposition") == disp
                   and it.get("reason") for it in items)

    drop_ok = (_has("1.10_commissions", "never-class")
              and _has("1.12_snags", "never-class")
              and _has("1.12_refusals", "never-class")
              and _has("1.7_track_record", "drop-with-reason"))
    if not drop_ok:
        failures.append("DROP-NEVER-SILENT: a NEVER-class or drop-with-reason specimen is missing "
                        "its own manifest line (silently absent rather than recorded-as-dropped)")
    print(f"DROP-NEVER-SILENT: commission/snag/write_refused (never-class) and review "
          f"(drop-with-reason) each present as their own manifest line with a reason -- "
          f"{'PASS' if drop_ok else 'FAIL'}")

    # -------------------------------------------------------------- RED-INGEST-UNREVIEWED (ii)
    tgt_dep = tgt_dir / "deployment.json"
    tgt_schema = json.loads(tgt_dep.read_text())["schema"]
    before = _ledger_count(tgt_schema)
    r = _ingest(manifest, tgt_dep, "author")
    after = _ledger_count(tgt_schema)
    refused = r.returncode == 1 and "REFUSED WHOLESALE" in r.stderr
    untouched = after == before
    if not (refused and untouched):
        failures.append(f"RED-INGEST-UNREVIEWED: exit={r.returncode} refused={refused} "
                        f"rows {before}->{after} (expected unchanged)\n{r.stderr}")
    print(f"RED-INGEST-UNREVIEWED: exit={r.returncode} (expect 1, REFUSED WHOLESALE), target rows "
          f"unchanged ({before}->{after}) -- {'PASS' if refused and untouched else 'FAIL'}")

    # -------------------------------------------------------------- GREEN-INGEST-ATTRIBUTED (iii)
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(json.dumps({"record": "review", "reviewed": True, "reviewer": "fixture-reviewer",
                            "ts": "2026-07-22T00:00:00Z", "note": "fixture review"}) + "\n")
    r = _ingest(manifest, tgt_dep, "author")
    ingest_ok = r.returncode in (0, 1)  # 1 is expected here too (duplicate-slug etc. among drops)
    rows = _psql("-tAc", f"""
        SELECT l.id, p.name FROM {tgt_schema}.ledger l
        JOIN {tgt_schema}_kernel.principal p ON p.id = l.actor
        WHERE l.kind IN ('decision','question','work_opened') ORDER BY l.id;
    """)
    written = [ln.split("|") for ln in rows.stdout.strip("\n").splitlines() if ln]
    all_attributed = len(written) >= 1 and all(name == "author" for _id, name in written)
    if not all_attributed:
        failures.append(f"GREEN-INGEST-ATTRIBUTED: not every carried row attributes to 'author' "
                        f"(the --actor passed): {written}")
    print(f"GREEN-INGEST-ATTRIBUTED: {len(written)} carried row(s) written, every one attributed "
          f"to actor='author' -- {'PASS' if all_attributed else 'FAIL'}")

    # -------------------------------------------------------------- PRE-S36-FALLBACK (vi)
    # Simulate a pre-s36 kernel by dropping the standing_decisions VIEW ONLY (the s36 delta's
    # decision_grade column and the kind=decision rows underneath stay untouched) -- this fixture's
    # job is to exercise extract_context's own _relation_exists(standing_decisions) branch, the
    # SAME probe production code runs against a genuinely pre-s36 world like this repo's own
    # autoharn1 (row 1950's live commission); it is not this fixture's job to birth a whole second
    # kernel lineage chain when dropping the one view already produces the exact input shape the
    # code branches on.
    src_schema = json.loads(src_dep.read_text())["schema"]
    _psql("-v", "ON_ERROR_STOP=1", "-c", f"DROP VIEW {src_schema}.standing_decisions;")
    fallback_manifest = tmpdir / "m_fallback.jsonl"
    r = _extract(src_dep, fallback_manifest)
    fb_items = [json.loads(l) for l in fallback_manifest.read_text(encoding="utf-8").splitlines()] \
        if r.returncode == 0 else []
    fb_decisions = [it for it in fb_items if it.get("record") == "item"
                    and it.get("class") == "1.2_standing_decisions"]
    fb_summary = [it for it in fb_items if it.get("record") == "class-summary"
                  and it.get("class") == "1.2_standing_decisions"]
    fallback_ok = (
        r.returncode == 0
        and len(fb_decisions) >= 2  # the "Standing rule ALPHA" + "ordinary undurable" rows seeded above
        and all(it.get("disposition") == "carry-verbatim" and it.get("grade") is None
                and it.get("dust_row_ids") for it in fb_decisions)
        and len(fb_summary) == 1
        and "s36" in (fb_summary[0].get("reason") or "")
        and fb_summary[0].get("count") == len(fb_decisions)
    )
    if not fallback_ok:
        failures.append(f"PRE-S36-FALLBACK: fallback extraction did not produce the expected "
                        f"carry-verbatim/no-grade items + class-summary (exit={r.returncode})\n"
                        f"decisions={fb_decisions}\nsummary={fb_summary}\nstderr={r.stderr}")
    print(f"PRE-S36-FALLBACK: standing_decisions absent -> {len(fb_decisions)} kind=decision "
          f"row(s) from ledger_current carried verbatim with grade=None, 1 class-summary naming "
          f"the widening -- {'PASS' if fallback_ok else 'FAIL'}")

    if failures:
        print(f"\nextract-context fixture: {len(failures)} FAILURE(S) -- scratch substrate left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n  source: {SRC_NAME} (db {DB}@{PGHOST})\n"
              f"  target: {TGT_NAME} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch(SRC_NAME)
    _drop_scratch(TGT_NAME)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nextract-context fixture: all cases PASS, scratch substrate torn down to zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
