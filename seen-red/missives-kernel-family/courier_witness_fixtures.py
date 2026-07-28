#!/usr/bin/env python3
"""Seen-red specimen for THREE courier findings across two strengthened-tier review laps,
serving axis:

MODERATE-SILENT, lap 2 round 1 (courier:123-207, batch-witness loss, ORIGINAL shape): when
`_require()` raises on row N mid-batch, earlier rows' outcomes (accepted AND refused) in the
SAME run vanished from the operator-facing report -- the reviewer witnessed a kernel-refused
row 1 reported NOWHERE on stdout when row 2 tripped `_require()`. FIX (round 1, since
superseded -- see the SEVERE-SILENT entry below): `run_counterpart()` accumulated a per-row
`outcomes` list AS PROCESSED and, on a mid-batch `_require()` raise, printed the accumulated
outcomes via `_print_batch_report()` before the exception propagated.

MODERATE-LOUD (courier:226-277, per-counterpart exit-code collapse): counterpart-side
`ProtocolVersionMismatch`/`BoundaryUnreachable`/`BoundaryRefusal`/`CourierConfigError` all
collapsed to exit 1, defeating bcc's own exit-code class discipline (0/1/3/4). FIX: `main()`
now tags each counterpart failure with bcc's own code for its class and, if every failure this
run belongs to ONE class, exits with THAT code; mixed classes exit 1 with a stderr line
enumerating every class seen.

SEVERE-SILENT, lap 2 round 2 (the fix round on THIS delta, ledger row 1263's build): round 1's
fix above only wrapped `_require()`'s payload-construction calls in try/except --
`bcc.post_write()`, called right after and OUTSIDE that try, can raise `BoundaryRefusal` (any
non-200 -- a transient 503/429 mid-batch is realistic, not an edge case) or `BoundaryUnreachable`
(a dropped connection) on ANY row N, reproducing the EXACT SAME loss class round 1's own
docstring claimed closed. FIX (this round, SUPERSEDING round 1's per-site guard, not layered on
top of it): one enclosing try/finally around the WHOLE per-row loop, keyed on a `completed` flag
-- `_print_batch_report` runs in `finally` whenever the loop did not run to completion, for ANY
reason, foreclosing the class at the shape level rather than guarding it at each site a reviewer
happens to find.

MODERATE-SILENT residue (re-lap review, fix round, 2026-07-26): every scenario above reproduces
a FAILURE; nothing asserted the converse -- that a fully successful batch prints NO
"BATCH ABORTED" banner. Closed by `all_accepted_batch_case()`: a GREEN positive control (an
all-accepted, ≥2-row batch through the real self boundary) plus a RED-capability demonstration
against `_completed_flag_broken_courier`'s copy (the `completed` flag's initializer flipped
`False` -> `True`, the review's own named example) -- witnessed silently dropping row 1's
abort-time outcome on the SAME `_BatchLossHandler` scenario `batch_witness_loss_case` already
uses, where the real, unmutated courier still reports it.

All three (plus the residue above) reproduced RED against either a deliberately reverted (never committed, discarded)
copy of the pre-fix code, or the byte-identical 8a2d25e commit (fetched via `git show`, never
hand-reconstructed) -- and GREEN against the real, current `courier` -- a REAL boundary_service.py
instance (scratch port, never 8433/8422) plus REAL mock counterpart (and, for the round-2
finding, mocked self -- see `_SelfMidBatchRefusalHandler`'s own docstring for why) HTTP servers
(stdlib http.server, not stubbed at the Python-object level) reproducing each exact scenario the
reviewer's own fixed report describes.
"""
from __future__ import annotations

import ast
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE = os.path.join(REPO, "kernel", "lineage")
COURIER = os.path.join(REPO, "libexec", "autoharn", "courier")  # relocated 2026-07-26 by work
# item courier-umbrella-rebase (ledger rows 1369/1370): courier now lives under
# libexec/autoharn/, not the repo root -- this constant repointed, everything downstream reads
# from it unchanged.
SERVING = os.path.join(REPO, "serving")
# FILING -- added 2026-07-26 by work item courier-umbrella-rebase (ledger rows 1369/1370):
# the relocated courier now also imports filing/fixture_sandbox.py (the established
# libexec/autoharn/* convention). The throwaway copies of courier's CURRENT body this fixture
# writes to /tmp (_reverted_courier_no_batch_report, _completed_flag_broken_courier) no longer
# sit next to serving/ OR filing/ on disk, so their own REPO_ROOT-relative sys.path.insert calls
# resolve to nothing at runtime -- exactly the same reason SERVING is already injected via
# PYTHONPATH below for those two throwaway invocations; FILING needs the identical treatment or
# `import fixture_sandbox` raises ModuleNotFoundError in a copy this fixture itself constructed.
# The historical 8a2d25e copy (_at_8a2d25e_courier) predates fixture_sandbox entirely and does
# not need this.
FILING = os.path.join(REPO, "filing")

CHAIN = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql", "s38-bookkeeping-close.sql",
    "s39-blocks-start.sql", "s40-principal-identity-events.sql",
    "s41-principal-bindings-and-relations.sql", "s42-row-hash-full-coverage.sql",
    "s43-typed-verdict-write-boundary.sql", "s45-standing-lifecycle.sql",
    "s44-model-identity-attestation.sql", "s46-credited-views.sql",
    "s47-claim-on-closed-refusal.sql", "s48-review-witness-existence.sql",
    "s49-journaler-overflow-guard.sql", "s50-defeat-input-raw-domain.sql",
    "s51-artifact-store.sql", "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
]

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {role} LOGIN;"])
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", os.path.join(LINEAGE, f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def dosql(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"SQL failed:\n{cp.stdout}\n{cp.stderr}")
    return cp.stdout + cp.stderr


def birth(schema: str, kern: str, role: str, wname: str) -> None:
    genesis = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis}') "
        f"ON CONFLICT (only_one) DO NOTHING;"])
    login_role = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", "SELECT session_user;"]).stdout.strip()
    dosql(schema, kern, role, f"""
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_registered', 'statement', 'author self-attributed',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_purpose', 'courier witness fixture'));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for drole in (role, login_role):
        dosql(schema, kern, role, f"""
SELECT set_config('birth.drole', '{drole}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_standing_declared', 'statement', 'standing',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_db_role', current_setting('birth.drole'),
    'principal_binding_active', true));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for pname, pclass in (("write-boundary", "tool"), ("courier", "tool")):
        dosql(schema, kern, role, f"""
SELECT set_config('birth.pname', '{pname}', false), set_config('birth.pclass', '{pclass}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.registration_write(jsonb_build_object(
    'name', current_setting('birth.pname'), 'agent_class', current_setting('birth.pclass'),
    'purpose', 'courier witness fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION '% registration refused: %', current_setting('birth.pname'), v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


# ------------------------------------------------------------------------------------------
# Mock counterpart HTTP servers (real sockets, stdlib http.server -- not Python-level stubs).
# ------------------------------------------------------------------------------------------

class _BatchLossHandler(BaseHTTPRequestHandler):
    """world=mockworld: row 1 has a malformed missive_provenance (real kernel refusal on the
    self side); row 2 is missing 'missive_act' entirely (courier's own _require())."""
    ROW1 = {"id": 1, "ts": "2026-07-25T00:00:00+00:00", "statement": "row one",
            "missive_act": "request", "missive_seq": 1, "missive_cites": None,
            "missive_thread": "mockworld/batch-1", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld:1:ZZZZ",
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld", "missive_addressee_world": "selfworld"}
    ROW2 = {"id": 2, "ts": "2026-07-25T00:00:01+00:00", "statement": "row two",
            "missive_seq": 2, "missive_cites": None,
            "missive_thread": "mockworld/batch-2", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld:2:" + "a" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld", "missive_addressee_world": "selfworld"}

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/mockworld/health"):
            body = json.dumps({"world": "mockworld", "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
        elif self.path.startswith("/d/mockworld/views/missive_outbound"):
            body = (json.dumps([self.ROW1, self.ROW2]).encode()
                    if "after_id=0" in self.path or "after_id=" not in self.path
                    else json.dumps([]).encode())
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class _MidBatchOutboundHandler(BaseHTTPRequestHandler):
    """world=mockworld2: TWO well-formed outbound rows addressed to selfworld -- both pass
    courier's own _require() cleanly (unlike _BatchLossHandler above, this scenario's defect
    lives entirely on the SELF side, not in a drifted counterpart shape)."""
    ROW1 = {"id": 1, "ts": "2026-07-25T00:00:00+00:00", "statement": "row one, mid-batch",
            "missive_act": "request", "missive_seq": 1, "missive_cites": None,
            "missive_thread": "mockworld2/mb-1", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld2:1:" + "b" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld2", "missive_addressee_world": "selfworld"}
    ROW2 = {"id": 2, "ts": "2026-07-25T00:00:01+00:00", "statement": "row two, mid-batch",
            "missive_act": "request", "missive_seq": 2, "missive_cites": None,
            "missive_thread": "mockworld2/mb-2", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld2:2:" + "c" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld2", "missive_addressee_world": "selfworld"}

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/mockworld2/health"):
            body = json.dumps({"world": "mockworld2", "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
        elif self.path.startswith("/d/mockworld2/views/missive_outbound"):
            body = (json.dumps([self.ROW1, self.ROW2]).encode()
                    if "after_id=0" in self.path or "after_id=" not in self.path
                    else json.dumps([]).encode())
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class _SelfMidBatchRefusalHandler(BaseHTTPRequestHandler):
    """Stands in as courier's OWN boundary (`self_base`), mocked deliberately (unlike the two
    cases above, which run against a REAL boundary_service.py instance) -- this scenario needs
    precise control over the SELF-side write response per row, which a real kernel would never
    manufacture on demand (a transient 503/429 from the kernel's own boundary is a realistic
    infrastructure event, not something `kernel.ledger_write` can be coaxed into producing for a
    specific row in a fixture). Row 1's write is accepted (200); row 2's write is refused at the
    BOUNDARY (503, a `BoundaryRefusal` -- OUTSIDE any try/except courier's own `_require()` ever
    guarded, finding 2's exact reproduction). `WRITE_COUNT` is a per-subclass counter (each case
    below mints a fresh subclass via `type()` so RED and GREEN each start at zero)."""
    WRITE_COUNT = 0

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/selfworld/health"):
            body = json.dumps({"world": "selfworld", "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
        elif self.path.startswith("/d/selfworld/standing/principals"):
            body = json.dumps([{"id": 1, "name": "courier", "agent_class": "tool"}]).encode()
        elif self.path.startswith("/d/selfworld/views/missive_receipts"):
            body = json.dumps([]).encode()  # nothing recorded yet -- high_water stays 0.
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/d/selfworld/write/ledger":
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)  # drain the request body -- its contents are not this scenario's point.
        type(self).WRITE_COUNT += 1
        if type(self).WRITE_COUNT == 1:
            self.send_response(200)
            body = json.dumps({"disposition": "accepted", "row_id": 100,
                               "sqlstate": None, "refusal_id": None, "message": None}).encode()
        else:
            self.send_response(503)  # a transient boundary refusal -- BoundaryRefusal, non-200.
            body = json.dumps({"detail": "simulated transient boundary failure "
                                          "(e.g. a 503/429) mid-batch"}).encode()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class _AllAcceptedHandler(BaseHTTPRequestHandler):
    """world=mockworld3: POSITIVE CONTROL for the batch-witness fix (fix round, re-lap review
    residue, MODERATE-SILENT: every OTHER scenario in this file reproduces a FAILURE -- nothing
    asserted the converse, that a fully successful batch prints NO "BATCH ABORTED" banner). Both
    rows are entirely well-formed and distinct (different threads/seqs), so both accept cleanly
    through the real self boundary with no mid-batch abort of any kind."""
    ROW1 = {"id": 1, "ts": "2026-07-26T00:00:00+00:00", "statement": "row one, all-accepted",
            "missive_act": "request", "missive_seq": 1, "missive_cites": None,
            "missive_thread": "mockworld3/ok-1", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld3:1:" + "d" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld3", "missive_addressee_world": "selfworld"}
    ROW2 = {"id": 2, "ts": "2026-07-26T00:00:01+00:00", "statement": "row two, all-accepted",
            "missive_act": "request", "missive_seq": 2, "missive_cites": None,
            "missive_thread": "mockworld3/ok-2", "missive_protocol": 1,
            "missive_provenance": "xrow:mockworld3:2:" + "e" * 64,
            "missive_disposition": None, "missive_responds_to": None,
            "missive_author_world": "mockworld3", "missive_addressee_world": "selfworld"}

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/mockworld3/health"):
            body = json.dumps({"world": "mockworld3", "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
        elif self.path.startswith("/d/mockworld3/views/missive_outbound"):
            body = (json.dumps([self.ROW1, self.ROW2]).encode()
                    if "after_id=0" in self.path or "after_id=" not in self.path
                    else json.dumps([]).encode())
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class _RefusalHandler(BaseHTTPRequestHandler):
    """world configurable via class attribute WORLD -- health OK, outbound 404s."""
    WORLD = "refusalworld"

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith(f"/d/{self.WORLD}/health"):
            body = json.dumps({"world": self.WORLD, "service_principal": None,
                               "capabilities": {}, "protocol_version": "1",
                               "authn_mode": "single-operator"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        elif self.path.startswith(f"/d/{self.WORLD}/views/missive_outbound"):
            self.send_response(404); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(b'{"detail":"unknown_view (mock refusal)"}')
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')


def _make_refusal_handler(world: str) -> type:
    return type(f"_RefusalHandler_{world}", (_RefusalHandler,), {"WORLD": world})


class _SkewHandler(BaseHTTPRequestHandler):
    """world=skewworld: health answers a WRONG protocol_version."""
    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/d/skewworld/health"):
            body = json.dumps({"world": "skewworld", "service_principal": None,
                               "capabilities": {}, "protocol_version": "999",
                               "authn_mode": "single-operator"}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers(); self.wfile.write(b'{"detail":"nf"}')


def _serve(handler_cls: type) -> tuple[HTTPServer, int]:
    srv = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = srv.server_address[1]
    t = Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _wait_up(port: int, path: str) -> None:
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=0.2)
            return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError(f"mock server on port {port} never came up")


def _run_courier(courier_path: str, toml_path: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    # FIXTURE-SANDBOX WAIVER (added 2026-07-26, work item courier-umbrella-rebase, ledger rows
    # 1369/1370): the relocated courier now imports filing/fixture_sandbox.py (the established
    # libexec/autoharn/* convention) and this WHOLE family's own run_fixtures.py sets
    # AUTOHARN_FIXTURE_SANDBOX=1 unconditionally (inherited by every subprocess this file spawns,
    # including this one) -- so every real courier invocation below would otherwise be refused.
    # REVIEWED reason: courier here is always pointed at self_base/counterpart_base URLs this
    # SAME fixture spins up itself (127.0.0.1 mock HTTP servers, see `_serve()`), never this
    # repo's own live deployment.json -- exactly the "use-site reason to touch a repo-root verb
    # directly" the waiver mechanism's own teach-text names as sanctioned.
    env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
        "courier_witness_fixtures.py: courier-toml points only at scratch 127.0.0.1 mock "
        "boundaries this same fixture spawns and tears down, never the real deployment.json")
    return sh(["python3", courier_path, "--courier-toml", toml_path], env=env, cwd=REPO)


def _write_toml(path: str, self_base: str, counterparts: dict[str, str]) -> None:
    lines = ["[courier]", 'authn = "single-operator"', 'self = "selfworld"',
             f'self_base = "{self_base}"', "", "[courier.counterparts]"]
    for name, base in counterparts.items():
        lines.append(f'{name} = "{base}"')
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _reverted_courier_no_batch_report(tmp_path: str) -> None:
    """A throwaway copy of `courier` with BOTH batch-witness-loss fixes reverted (no `outcomes`
    accumulation, no `_print_batch_report` call at all) -- reproduces the ORIGINAL, round-1
    finding (a mid-batch `_require()` raise loses every earlier row's outcome outright). The
    `old` text below is matched against the CURRENT tree's `run_counterpart` (round-2 shape:
    the enclosing try/finally, finding 2's own fix) so this stays in sync as courier's own body
    evolves; the SEPARATE round-2 regression (a mid-batch `post_write()` raise, outside any
    `_require()`-scoped try/except) is reproduced by `post_write_midbatch_refusal_case` below
    against the byte-identical 8a2d25e commit fetched from git history, not a hand-edited copy
    of this file's own `old`/`new` strings -- two different priors, two different mechanisms.
    Never committed; discarded after use."""
    with open(COURIER) as f:
        text = f.read()
    old = '''    outcomes: list[str] = []
    completed = False
    try:
        for r in candidates:
            payload = {
                "kind": "missive_received",
                "statement": _require(r, "statement", route=outbound_route, counterpart=counterpart),
                "actor": actor_id,
                "missive_protocol": _require(r, "missive_protocol", route=outbound_route, counterpart=counterpart),
                "missive_author_world": _require(r, "missive_author_world", route=outbound_route, counterpart=counterpart),
                "missive_addressee_world": _require(r, "missive_addressee_world", route=outbound_route, counterpart=counterpart),
                "missive_thread": _require(r, "missive_thread", route=outbound_route, counterpart=counterpart),
                "missive_seq": _require(r, "missive_seq", route=outbound_route, counterpart=counterpart),
                "missive_act": _require(r, "missive_act", route=outbound_route, counterpart=counterpart),
                "missive_provenance": _require(r, "missive_provenance", route=outbound_route, counterpart=counterpart),
            }
            if r.get("missive_responds_to") is not None:
                payload["missive_responds_to"] = r["missive_responds_to"]
            if r.get("missive_cites") is not None:
                payload["missive_cites"] = r["missive_cites"]
            # missive_disposition rides ONLY on acknowledgment missives (spec §2.3 note ²'s
            # second licensed home) -- omitted here until 2026-07-28, when the FIRST live ack
            # crossing refused on missive_disposition_mandatory_on_ack (autoharn3 row 131):
            # the "served envelope columns verbatim" contract was false by exactly this column.
            if r.get("missive_disposition") is not None:
                payload["missive_disposition"] = r["missive_disposition"]
            exit_code, verdict = bcc.post_write(f"{self_base}/d/{self_name}", "ledger", payload)
            if exit_code == 0:
                recorded.append(verdict["row_id"])
                outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                                f"seq={r['missive_seq']}: accepted (recorded row_id={verdict['row_id']})")
            else:
                msg = verdict.get("message") or ""
                if "already exists" in msg and "exactly-once RECORDING" in msg:
                    dedup_raced += 1  # the race backstop, spec §5 step 3 -- logged, pass continues.
                    outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                                    f"seq={r['missive_seq']}: refused (dedup race, idempotent)")
                else:
                    errors.append(
                        f"missive (thread={r['missive_thread']!r} seq={r['missive_seq']}) refused "
                        f"NOT as a dedup race: {msg}")
                    outcomes.append(f"row id={r['id']} thread={r['missive_thread']!r} "
                                    f"seq={r['missive_seq']}: refused (NOT dedup): {msg}")
        completed = True
    finally:
        if not completed:
            _print_batch_report(counterpart, outcomes)

    return {
        "pulled": len(outbound), "new": len(candidates),
        "recorded": recorded, "dedup_raced": dedup_raced, "errors": errors, "outcomes": outcomes,
    }'''
    # NOTE (hazard fix, found in reach of work item courier-ack-disposition-drop, row 131,
    # 2026-07-28): `old` above must stay byte-identical to courier's CURRENT `run_counterpart`
    # body, including the missive_disposition-forwarding block commit 86cb5c4 added -- this
    # revert only removes the outcomes/completed/finally batch-witness mechanism (round-1/round-2
    # fixes), never the row-131 forwarding fix, so `new` below keeps that block intact too.
    new = '''    for r in candidates:
        payload = {
            "kind": "missive_received",
            "statement": _require(r, "statement", route=outbound_route, counterpart=counterpart),
            "actor": actor_id,
            "missive_protocol": _require(r, "missive_protocol", route=outbound_route, counterpart=counterpart),
            "missive_author_world": _require(r, "missive_author_world", route=outbound_route, counterpart=counterpart),
            "missive_addressee_world": _require(r, "missive_addressee_world", route=outbound_route, counterpart=counterpart),
            "missive_thread": _require(r, "missive_thread", route=outbound_route, counterpart=counterpart),
            "missive_seq": _require(r, "missive_seq", route=outbound_route, counterpart=counterpart),
            "missive_act": _require(r, "missive_act", route=outbound_route, counterpart=counterpart),
            "missive_provenance": _require(r, "missive_provenance", route=outbound_route, counterpart=counterpart),
        }
        if r.get("missive_responds_to") is not None:
            payload["missive_responds_to"] = r["missive_responds_to"]
        if r.get("missive_cites") is not None:
            payload["missive_cites"] = r["missive_cites"]
        if r.get("missive_disposition") is not None:
            payload["missive_disposition"] = r["missive_disposition"]
        exit_code, verdict = bcc.post_write(f"{self_base}/d/{self_name}", "ledger", payload)
        if exit_code == 0:
            recorded.append(verdict["row_id"])
        else:
            msg = verdict.get("message") or ""
            if "already exists" in msg and "exactly-once RECORDING" in msg:
                dedup_raced += 1
            else:
                errors.append(
                    f"missive (thread={r['missive_thread']!r} seq={r['missive_seq']}) refused "
                    f"NOT as a dedup race: {msg}")

    return {
        "pulled": len(outbound), "new": len(candidates),
        "recorded": recorded, "dedup_raced": dedup_raced, "errors": errors,
    }'''
    if old not in text:
        raise RuntimeError("RED REPRO SETUP FAILED: batch-loss revert target text not found -- "
                            "courier's own body has changed shape; update this fixture.")
    with open(tmp_path, "w") as f:
        f.write(text.replace(old, new))


def _at_8a2d25e_courier(tmp_path: str) -> None:
    """The `courier` script BYTE-IDENTICAL to commit 8a2d25e (fetched via `git show`, never
    hand-reconstructed) -- the exact code the strengthened-tier review's finding 2 was raised
    against: `_require()`'s payload-construction calls are wrapped in try/except, but
    `bcc.post_write()` (called right after, OUTSIDE that try) is not, so a `BoundaryRefusal`/
    `BoundaryUnreachable` it raises on row N escapes uncaught with no batch-report flush. Never
    committed to this checkout; discarded after use."""
    cp = subprocess.run(["git", "show", "8a2d25e:courier"], capture_output=True, text=True,
                        cwd=REPO, check=True)
    if not cp.stdout.strip():
        raise RuntimeError("RED REPRO SETUP FAILED: `git show 8a2d25e:courier` returned nothing "
                            "-- this checkout's history does not contain that commit.")
    with open(tmp_path, "w") as f:
        f.write(cp.stdout)


def _completed_flag_broken_courier(tmp_path: str) -> None:
    """A throwaway copy of the CURRENT, real `courier` with exactly one line changed: the
    `completed` flag's initializer flipped `False` -> `True` -- the re-lap review's own named
    example of a future edit that "breaks the completed-flag logic" ("e.g. sets completed=True
    before the loop"). This does not touch the all-accepted positive control's own output (a
    clean run prints nothing either way, mutated or not -- the flag ends up True at the finally
    check regardless of when it was set); it is witnessed instead against `_BatchLossHandler`'s
    existing mid-batch-abort scenario, where the difference is stark: with the flag pre-set,
    `finally`'s `if not completed` guard reads false EVEN THOUGH THE LOOP NEVER REACHED ITS OWN
    `completed = True` line, so the abort's accumulated outcomes -- which the real, unmutated
    courier flushes via `_print_batch_report` -- are silently dropped entirely. Never committed;
    discarded after use."""
    with open(COURIER) as f:
        text = f.read()
    old = "    outcomes: list[str] = []\n    completed = False\n    try:"
    new = ("    outcomes: list[str] = []\n"
           "    completed = True  # BROKEN (fixture-injected): pre-set, see this file's "
           "_completed_flag_broken_courier docstring\n"
           "    try:")
    if old not in text:
        raise RuntimeError("RED REPRO SETUP FAILED: completed-flag initializer text not found -- "
                            "courier's own body has changed shape; update this fixture.")
    with open(tmp_path, "w") as f:
        f.write(text.replace(old, new))


def all_accepted_batch_case() -> None:
    """POSITIVE CONTROL closing the re-lap review's MODERATE-SILENT residue: every scenario
    above in this file reproduces a FAILURE; nothing asserted the converse -- that a fully
    successful batch (every row accepted, no mid-batch abort of any kind) prints NO
    "BATCH ABORTED" banner anywhere. A future edit that breaks the `completed`-flag logic in
    courier's `run_counterpart` try/finally (the review's own example: pre-setting the flag
    before the loop even starts) would sail through every check above -- none of them assert
    silence on a clean run, only that a BROKEN run's own particular two rows are reported.

    GREEN (the actual positive control): two well-formed, distinct rows (`_AllAcceptedHandler`)
    through the real self boundary (the SAME running `boundary_service.py` instance `main()`
    already started) -- asserts exit 0, both rows' outcomes appear in main()'s own
    one-line-per-counterpart summary (`recorded=[...]` with two entries), and the string
    "BATCH ABORTED" appears NOWHERE in stdout+stderr.

    RED-capability (the flag-mutation demonstration this fix round asked for, so the new check
    is not merely a check that could never fail): re-runs `_BatchLossHandler`'s own existing
    mid-batch-abort scenario (row 1 kernel-refused on a malformed provenance shape, row 2
    `_require`-refused on a missing field) against `_completed_flag_broken_courier`'s copy --
    with the flag pre-satisfied, NEITHER row 1's outcome NOR the "BATCH ABORTED" banner itself
    appears anywhere, even though the run still fails loudly (nonzero exit; the propagated
    `CourierConfigError` from row 2's `_require` is untouched by this mutation -- only the
    outcome WITNESS is lost). GREEN (same abort scenario, real unmutated courier): both the
    banner and row 1's outcome are present, confirming the MUTATION -- not the scenario -- is
    what causes the loss."""
    ok_srv, ok_port = _serve(_AllAcceptedHandler)
    try:
        _wait_up(ok_port, "/d/mockworld3/health")
        toml_ok = "/tmp/mkf_courier_allok.toml"
        _write_toml(toml_ok, f"http://127.0.0.1:{_SELF_PORT}",
                    {"mockworld3": f"http://127.0.0.1:{ok_port}"})
        cp = _run_courier(COURIER, toml_ok)
        out = cp.stdout + cp.stderr
        print("  positive control stdout+stderr:\n" + "\n".join(f"    {l}" for l in out.splitlines()))
        recorded_match = re.search(r"pulled=2 new=2 recorded=(\[[^\]]*\]) dedup-raced=0", out)
        # recorded=[...] carries real kernel-assigned row_ids (never the counterpart's own
        # served 'id' field, which is unrelated) -- checked by COUNT (two entries), not by value.
        _check("positive control: exit 0 on an all-accepted batch", cp.returncode == 0)
        _check("positive control: both rows' outcomes appear in the normal summary "
               "(recorded=[...] carries two row_id entries)",
               recorded_match is not None
               and len(ast.literal_eval(recorded_match.group(1))) == 2)
        _check('positive control: "BATCH ABORTED" appears NOWHERE for a fully successful batch',
               "BATCH ABORTED" not in out)
    finally:
        ok_srv.shutdown()

    # RED-capability: the SAME abort scenario _BatchLossHandler already provides (used above by
    # batch_witness_loss_case), now against a copy of courier with the completed flag broken.
    loss_srv, loss_port = _serve(_BatchLossHandler)
    try:
        _wait_up(loss_port, "/d/mockworld/health")
        toml_loss = "/tmp/mkf_courier_flagbroken.toml"
        _write_toml(toml_loss, f"http://127.0.0.1:{_SELF_PORT}", {"mockworld": f"http://127.0.0.1:{loss_port}"})

        broken_path = "/tmp/mkf_courier_flagbroken.py"
        _completed_flag_broken_courier(broken_path)
        broken_env = dict(os.environ)
        broken_env["PYTHONPATH"] = (SERVING + os.pathsep + FILING
                                     + os.pathsep + broken_env.get("PYTHONPATH", ""))
        # Same fixture-sandbox waiver as `_run_courier` above -- this throwaway copy of
        # courier's CURRENT body also imports fixture_sandbox and inherits the family's own
        # AUTOHARN_FIXTURE_SANDBOX=1 marker; same reviewed reason (scratch mock boundaries only).
        broken_env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
            "courier_witness_fixtures.py: courier-toml points only at scratch 127.0.0.1 mock "
            "boundaries this same fixture spawns and tears down, never the real deployment.json")
        cp = sh(["python3", broken_path, "--courier-toml", toml_loss], cwd=REPO, env=broken_env)
        red_out = cp.stdout + cp.stderr
        print("  RED (completed-flag broken) stdout+stderr:\n" +
              "\n".join(f"    {l}" for l in red_out.splitlines()))
        _check("RED (flag broken): the abort's own banner is now MISSING entirely, despite a "
               "genuine mid-batch abort", "BATCH ABORTED" not in red_out)
        _check("RED (flag broken): row 1's kernel-refusal outcome is ALSO silently lost "
               "(not merely the banner text)", "missive_provenance_shape" not in red_out)
        _check("RED (flag broken): the run still fails loudly (nonzero exit) -- only the "
               "outcome WITNESS is lost, not the failure itself", cp.returncode != 0)
        os.remove(broken_path)

        # GREEN: same scenario, real courier -- banner and row 1's outcome both present. Already
        # proven by batch_witness_loss_case above; re-asserted here so this case is self-
        # contained and its RED leg has a directly comparable GREEN leg in the SAME function.
        cp = _run_courier(COURIER, toml_loss)
        green_out = cp.stdout + cp.stderr
        print("  GREEN (real courier, same abort scenario) stdout+stderr:\n" +
              "\n".join(f"    {l}" for l in green_out.splitlines()))
        _check("GREEN: the real courier still prints the banner and row 1's outcome for the "
               "SAME abort scenario the broken copy silently ate",
               "BATCH ABORTED" in green_out and "missive_provenance_shape" in green_out)
    finally:
        loss_srv.shutdown()


def post_write_midbatch_refusal_case() -> None:
    """SEVERE-SILENT, the second courier finding (strengthened-tier review lap 2): the
    batch-witness fix landed in 8a2d25e only wraps `_require()`'s payload-construction calls in
    try/except -- `bcc.post_write()`, called right after and OUTSIDE that try, can raise
    `BoundaryRefusal` (any non-200 -- a transient 503/429 mid-batch is realistic, not an edge
    case) or `BoundaryUnreachable` (a dropped connection) on ANY row N; against 8a2d25e's own
    code that exception then escapes `run_counterpart` uncaught, `_print_batch_report` is never
    called, and every row before N's decided outcome (accepted or kernel-refused) is lost --
    reproducing the exact defect class the delta's own docstring claims closed.

    Reproduced here with row 1 accepted at courier's OWN self boundary (mocked -- see
    `_SelfMidBatchRefusalHandler`'s own docstring for why self is mocked in this one case) and
    row 2's write to that SAME self boundary refused (503): RED against the byte-identical
    8a2d25e commit (row 1's acceptance reported NOWHERE once row 2's post_write raises), GREEN
    against the current tree (the enclosing try/finally flushes row 1's outcome before the
    BoundaryRefusal propagates)."""
    counter_srv, counter_port = _serve(_MidBatchOutboundHandler)
    try:
        _wait_up(counter_port, "/d/mockworld2/health")
        toml_path = "/tmp/mkf_courier_midbatch.toml"

        # RED: courier AS COMMITTED AT 8a2d25e.
        red_path = "/tmp/mkf_courier_midbatch_8a2d25e.py"
        _at_8a2d25e_courier(red_path)
        red_self_cls = type("_SelfMidBatchRefusalHandlerRed", (_SelfMidBatchRefusalHandler,),
                            {"WRITE_COUNT": 0})
        red_srv, red_port = _serve(red_self_cls)
        try:
            _wait_up(red_port, "/d/selfworld/health")
            _write_toml(toml_path, f"http://127.0.0.1:{red_port}",
                        {"mockworld2": f"http://127.0.0.1:{counter_port}"})
            red_env = dict(os.environ)
            red_env["PYTHONPATH"] = SERVING + os.pathsep + red_env.get("PYTHONPATH", "")
            cp = sh(["python3", red_path, "--courier-toml", toml_path], cwd=REPO, env=red_env)
            red_out = cp.stdout + cp.stderr
            print("  RED (8a2d25e) stdout+stderr:\n" + "\n".join(f"    {l}" for l in red_out.splitlines()))
            _check("RED (8a2d25e): row 1's accepted outcome (row_id=100) is reported NOWHERE "
                   "once row 2's post_write is refused mid-batch",
                   "row_id=100" not in red_out)
            _check("RED (8a2d25e): the run still fails loudly (nonzero exit) -- it is the "
                   "SILENT LOSS of row 1's outcome that is the defect, not a missed failure",
                   cp.returncode != 0)
        finally:
            red_srv.shutdown()
        os.remove(red_path)

        # GREEN: the real, current courier -- row 1's outcome must survive the propagated
        # BoundaryRefusal from row 2's post_write.
        green_self_cls = type("_SelfMidBatchRefusalHandlerGreen", (_SelfMidBatchRefusalHandler,),
                              {"WRITE_COUNT": 0})
        green_srv, green_port = _serve(green_self_cls)
        try:
            _wait_up(green_port, "/d/selfworld/health")
            _write_toml(toml_path, f"http://127.0.0.1:{green_port}",
                        {"mockworld2": f"http://127.0.0.1:{counter_port}"})
            cp = _run_courier(COURIER, toml_path)
            green_out = cp.stdout + cp.stderr
            print("  GREEN stdout+stderr:\n" + "\n".join(f"    {l}" for l in green_out.splitlines()))
            _check("GREEN: row 1's accepted outcome (row_id=100) IS reported despite row 2's "
                   "mid-batch post_write refusal",
                   "recorded row_id=100" in green_out)
            _check("GREEN: the BoundaryRefusal itself still propagates and fails the run loudly "
                   "(exit 3, boundary-refused)", cp.returncode == 3)
        finally:
            green_srv.shutdown()
    finally:
        counter_srv.shutdown()


def batch_witness_loss_case(schema: str, kern: str, role: str) -> None:
    srv, port = _serve(_BatchLossHandler)
    try:
        _wait_up(port, "/d/mockworld/health")
        toml_path = "/tmp/mkf_courier_batch.toml"
        _write_toml(toml_path, f"http://127.0.0.1:{_SELF_PORT}", {"mockworld": f"http://127.0.0.1:{port}"})

        # RED: reverted copy -- row 1's kernel refusal must be reported NOWHERE.
        red_path = "/tmp/mkf_courier_batch_reverted.py"
        _reverted_courier_no_batch_report(red_path)
        red_env = dict(os.environ)
        red_env["PYTHONPATH"] = (SERVING + os.pathsep + FILING
                                  + os.pathsep + red_env.get("PYTHONPATH", ""))
        # Same fixture-sandbox waiver as `_run_courier` above -- this throwaway copy of
        # courier's CURRENT body also imports fixture_sandbox and inherits the family's own
        # AUTOHARN_FIXTURE_SANDBOX=1 marker; same reviewed reason (scratch mock boundaries only).
        red_env["AUTOHARN_FIXTURE_SANDBOX_WAIVER"] = (
            "courier_witness_fixtures.py: courier-toml points only at scratch 127.0.0.1 mock "
            "boundaries this same fixture spawns and tears down, never the real deployment.json")
        cp = sh(["python3", red_path, "--courier-toml", toml_path], cwd=REPO, env=red_env)
        red_out = cp.stdout + cp.stderr
        print("  RED stdout+stderr:\n" + "\n".join(f"    {l}" for l in red_out.splitlines()))
        _check("RED: row 1's kernel-refusal (provenance shape) is reported NOWHERE",
               "missive_provenance_shape" not in red_out)
        _check("RED: row 2's _require failure IS reported (the only visible outcome)",
               "missive_act" in red_out)
        os.remove(red_path)

        # GREEN: the real, current courier -- row 1's outcome must survive the mid-batch raise.
        cp = _run_courier(COURIER, toml_path)
        green_out = cp.stdout + cp.stderr
        print("  GREEN stdout+stderr:\n" + "\n".join(f"    {l}" for l in green_out.splitlines()))
        _check("GREEN: row 1's kernel-refusal (provenance shape) IS reported",
               "missive_provenance_shape" in green_out)
        _check("GREEN: row 2's _require failure is ALSO reported",
               "missive_act" in green_out)
        _check("GREEN: exit code is 1 (config-error class, uniform)", cp.returncode == 1)
    finally:
        srv.shutdown()


def exit_code_aggregation_cases(schema: str, kern: str, role: str) -> None:
    skew_srv, skew_port = _serve(_SkewHandler)
    refusal_srv, refusal_port = _serve(_make_refusal_handler("refusalworld"))
    refusal2_srv, refusal2_port = _serve(_make_refusal_handler("refusalworld2"))
    mock_srv, mock_port = _serve(_BatchLossHandler)
    dead_port = 1  # nothing listens on port 1 as an unprivileged user -- BoundaryUnreachable.
    try:
        _wait_up(skew_port, "/d/skewworld/health")
        _wait_up(refusal_port, "/d/refusalworld/health")
        _wait_up(refusal2_port, "/d/refusalworld2/health")
        _wait_up(mock_port, "/d/mockworld/health")

        # Scenario A: uniform class 4 (version mismatch + unreachable) -> exit 4.
        toml_a = "/tmp/mkf_courier_A.toml"
        _write_toml(toml_a, f"http://127.0.0.1:{_SELF_PORT}",
                    {"skewworld": f"http://127.0.0.1:{skew_port}",
                     "deadworld": f"http://127.0.0.1:{dead_port}"})
        cp = _run_courier(COURIER, toml_a)
        print(f"  scenario A (uniform class 4): exit={cp.returncode}")
        print("    " + (cp.stdout + cp.stderr).replace("\n", "\n    "))
        _check("scenario A: uniform boundary-unreachable/version-mismatch -> exit 4",
               cp.returncode == 4)

        # Scenario B: uniform class 3 (both counterparts BoundaryRefusal) -> exit 3.
        toml_b = "/tmp/mkf_courier_B.toml"
        _write_toml(toml_b, f"http://127.0.0.1:{_SELF_PORT}",
                    {"refusalworld": f"http://127.0.0.1:{refusal_port}",
                     "refusalworld2": f"http://127.0.0.1:{refusal2_port}"})
        cp = _run_courier(COURIER, toml_b)
        print(f"  scenario B (uniform class 3): exit={cp.returncode}")
        print("    " + (cp.stdout + cp.stderr).replace("\n", "\n    "))
        _check("scenario B: uniform boundary-refused -> exit 3", cp.returncode == 3)

        # Scenario C: mixed classes (4, 3, 1) -> exit 1 with an enumeration line.
        toml_c = "/tmp/mkf_courier_C.toml"
        _write_toml(toml_c, f"http://127.0.0.1:{_SELF_PORT}",
                    {"deadworld": f"http://127.0.0.1:{dead_port}",
                     "refusalworld": f"http://127.0.0.1:{refusal_port}",
                     "mockworld": f"http://127.0.0.1:{mock_port}"})
        cp = _run_courier(COURIER, toml_c)
        out = cp.stdout + cp.stderr
        print(f"  scenario C (mixed): exit={cp.returncode}")
        print("    " + out.replace("\n", "\n    "))
        _check("scenario C: mixed classes -> exit 1", cp.returncode == 1)
        _check("scenario C: stderr enumerates all three classes seen",
               all(tag in out for tag in ("4 (", "3 (", "1 (")) and "MIXED" in out)
    finally:
        skew_srv.shutdown()
        refusal_srv.shutdown()
        refusal2_srv.shutdown()
        mock_srv.shutdown()


_SELF_PORT = 0


def main() -> int:
    global _SELF_PORT
    suffix = "mkfcourier"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)
    boundary_proc = None
    try:
        apply_chain(schema, kern, role)
        birth(schema, kern, role, "selfworld")

        toml_path = "/tmp/mkf_courier_multiplex.toml"
        with open(toml_path, "w") as f:
            f.write(f"""[deployments.selfworld]
pghost = "{PGHOST}"
pgdatabase = "{PGDB}"
pguser = "{role}"
pgschema = "{schema}"
pgkern = "{kern}"
""")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        _SELF_PORT = s.getsockname()[1]
        s.close()
        boundary_proc = subprocess.Popen(
            ["python3", "boundary_service.py", "--config", toml_path,
             "--port", str(_SELF_PORT)],
            cwd=SERVING, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _wait_up(_SELF_PORT, f"/d/selfworld/health")

        print("### batch-witness-loss (moderate-silent)")
        batch_witness_loss_case(schema, kern, role)
        print("\n### exit-code aggregation (moderate-loud)")
        exit_code_aggregation_cases(schema, kern, role)
        print("\n### post_write-time mid-batch refusal (severe-silent, lap 2 finding 2)")
        # Self-contained (both self AND counterpart mocked -- see post_write_midbatch_refusal_
        # case's own docstring for why); does not touch the real boundary_proc/schema above.
        post_write_midbatch_refusal_case()
        print("\n### all-accepted batch positive control (moderate-silent residue, fix round)")
        # Uses the real boundary_proc/schema above (via the module-global _SELF_PORT) for its
        # GREEN leg, and _BatchLossHandler's existing abort scenario for its RED-capability leg.
        all_accepted_batch_case()
    finally:
        if boundary_proc is not None:
            boundary_proc.terminate()
            boundary_proc.wait(timeout=10)
        teardown(schema, kern, role)

    if FAILURES:
        print(f"\ncourier_witness_fixtures: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\ncourier_witness_fixtures: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
