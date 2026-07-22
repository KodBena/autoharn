#!/usr/bin/env python3
"""Both-polarity fixture for tools/strip_provenance_banners.py (gates/fixture_census.py
REGISTRY entry "strip-provenance-banners"). The banner is retired (ledger row 1903/1904);
this fixture proves the RETIREMENT TOOL itself does not eat file content that merely
resembles a banner, does not mangle a hand-damaged real banner, and is idempotent.

Real infra, no mocks: every case below runs the actual `tools/strip_provenance_banners.py`
as a subprocess against real files in a real temp directory (never a mocked filesystem), then
reads the files back off disk to check the result (ADR-0013 Rule 5: verify the artifact, not
the claim). `git ls-files` is what the tool walks, so each temp case is its own throwaway git
repo with the specimen files staged/committed.

Cases:
  a-content-mention-preserved   -- RED (what a naive bare-substring stripper would eat): a
                                    Python file whose comment PROSE mentions the begin-marker
                                    text but is not followed by the other 4 banner-shaped
                                    lines. Must be left byte-identical; the tool's structural,
                                    exact-shape recognizer is what protects it.
  b-malformed-banner-flagged    -- a REAL banner with one hand-introduced typo (an extra space
                                    before the "last-change" colon, the exact shape witnessed
                                    live in this repo's own tools/setup_tui/ui_textual.py and
                                    seen-red/setup-tui-textual-shell/run_fixtures.py at strip
                                    time) must be classified 'damaged' and left untouched --
                                    flagged for manual adjudication, never silently mangled.
  c-idempotent-second-run       -- baseline: a file with a real, well-formed banner is
                                    stripped on the first run; a second run over the
                                    already-stripped tree finds nothing left to do (exit 0,
                                    zero further files touched).

Zero residue: the whole temp directory is removed in `finally` regardless of outcome.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "strip_provenance_banners.py"

# Assembled from split literals ON PURPOSE, same idiom as the tool under test and
# hooks/stamp_provenance.py: the contiguous marker text must not appear in this fixture's own
# source, so a live strip pass over THIS file (while it is being authored) cannot mistake this
# file's own definition of the marker for a banner needing protection.
_MARK = "PROV" "ENANCE-STAMP"
BEGIN = f">>> {_MARK} >>>"
END = f"<<< {_MARK} <<<"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _run_tool(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    # The tool walks `git -C <root> ls-files` from its own ROOT (parents[1] of its own file),
    # which is a hard-coded repo-root-relative resolution -- so each case runs it with cwd
    # irrelevant to the tool's own root resolution, but the throwaway repo must instead BE
    # what the tool treats as ROOT. We invoke it via `python3 <copied-tool> ...` with the
    # copy's own parents[1] landing on the throwaway repo, by placing the copy at
    # <tmp>/tools/strip_provenance_banners.py -- mirrors the real repo layout exactly, so the
    # tool's own `Path(__file__).resolve().parents[1]` resolves to <tmp>, not REPO.
    tool_copy = cwd / "tools" / "strip_provenance_banners.py"
    return subprocess.run([sys.executable, str(tool_copy), *args], cwd=cwd,
                           capture_output=True, text=True)


def _mk_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="strip-prov-fixture-"))
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "fixture@example.invalid")
    _git(d, "config", "user.name", "fixture")
    (d / "tools").mkdir()
    (d / "tools" / "strip_provenance_banners.py").write_text(TOOL.read_text(encoding="utf-8"),
                                                              encoding="utf-8")
    return d


def case_a_content_preserved() -> None:
    d = _mk_repo()
    try:
        content = (
            "#!/usr/bin/env python3\n"
            f"# the banner marker {BEGIN} is how a real stamp begins\n"
            "value = 42\n"
        )
        f = d / "mentions.py"
        f.write_text(content, encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "seed")

        res = _run_tool(d, "--report")
        assert res.returncode == 0, res.stderr
        assert "would strip 0 real banner" in res.stdout, res.stdout
        assert "mentions.py" in res.stdout, res.stdout  # surfaced in the content/report bucket

        strip_res = _run_tool(d)
        assert strip_res.returncode == 0, strip_res.stderr
        assert "stripped 0 real banner" in strip_res.stdout, strip_res.stdout
        assert f.read_text(encoding="utf-8") == content, "content-mention file was mutated!"
        print("RED  ok: a-content-mention-preserved -- prose mention left byte-identical")
    finally:
        _rm(d)


def case_b_malformed_flagged() -> None:
    d = _mk_repo()
    try:
        content = (
            "#!/usr/bin/env python3\n"
            f"# {BEGIN} (auto; tools/hooks/stamp_provenance.py -- do not hand-edit)\n"
            "#   first-seen : 2026-07-19T00:00:00Z\n"
            "#   last-change : 2026-07-19T00:00:00Z\n"  # the witnessed typo: extra space
            "#   contributors: deadbeef/main\n"
            f"# {END}\n"
            "\n"
            "print('hello')\n"
        )
        f = d / "damaged.py"
        f.write_text(content, encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "seed")

        res = _run_tool(d, "--report")
        assert res.returncode == 0, res.stderr
        assert "damaged: 1 file" in res.stdout, res.stdout
        assert "damaged.py" in res.stdout, res.stdout

        strip_res = _run_tool(d)
        assert strip_res.returncode == 0, strip_res.stderr
        assert "stripped 0 real banner" in strip_res.stdout, strip_res.stdout
        assert f.read_text(encoding="utf-8") == content, "damaged banner was mangled, not refused!"
        print("RED  ok: b-malformed-banner-flagged -- hand-damaged banner refused untouched")
    finally:
        _rm(d)


def case_c_idempotent() -> None:
    d = _mk_repo()
    try:
        contributors = "deadbeef/main"
        content = (
            "#!/usr/bin/env python3\n"
            f"# {BEGIN} (auto; tools/hooks/stamp_provenance.py -- do not hand-edit)\n"
            "#   first-seen : 2026-07-19T00:00:00Z\n"
            "#   last-change: 2026-07-19T00:00:00Z\n"
            f"#   contributors: {contributors}\n"
            f"# {END}\n"
            "\n"
            "print('hello')\n"
        )
        f = d / "real.py"
        f.write_text(content, encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "seed")

        first = _run_tool(d)
        assert first.returncode == 0, first.stderr
        assert "stripped 1 real banner" in first.stdout, first.stdout
        stripped_text = f.read_text(encoding="utf-8")
        assert BEGIN not in stripped_text and END not in stripped_text, stripped_text
        assert stripped_text == "#!/usr/bin/env python3\nprint('hello')\n", stripped_text

        second = _run_tool(d)
        assert second.returncode == 0, second.stderr
        assert "stripped 0 real banner" in second.stdout, second.stdout
        assert f.read_text(encoding="utf-8") == stripped_text, "second run touched an already-stripped file"
        print("GREEN ok: c-idempotent-second-run -- strip then no-op, zero further churn")
    finally:
        _rm(d)


def _rm(d: Path) -> None:
    shutil.rmtree(d, ignore_errors=True)


def main() -> int:
    case_a_content_preserved()
    case_b_malformed_flagged()
    case_c_idempotent()
    print("ALL CASES OK -- strip-provenance-banners both polarities + idempotency, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
