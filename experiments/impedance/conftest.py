#!/usr/bin/env python
"""conftest.py — test scaffolding for the standalone `impedance` package.

Its presence at the package root puts the root on `sys.path`, so `import impedance`,
`from impedance.lib import ...`, and `from demo.pipeline import ...` resolve when pytest runs from
here. It also exposes two fixtures the typing tests use to drive `mypy --strict` as a subprocess
and read its diagnostics back — the mechanized form of the closure claim (ADR-0011 Rule 1).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_LINE_RE = re.compile(r"^[^:]+:(\d+): error: .*\[([a-z-]+)\]\s*$")
_EXPECT_RE = re.compile(r"#\s*EXPECT\[([a-z-]+)\]")


def _run_mypy_strict(target: str) -> dict[int, set[str]]:
    """Run `mypy --strict` on one file (relative to ROOT) and return {line -> {error codes}}."""
    env = dict(os.environ, MYPYPATH=str(ROOT))
    proc = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "--no-error-summary",
         "--show-error-codes", "--hide-error-context", target],
        cwd=str(ROOT), env=env, capture_output=True, text=True,
    )
    out: dict[int, set[str]] = {}
    for raw in proc.stdout.splitlines():
        m = _LINE_RE.match(raw)
        if m:
            out.setdefault(int(m.group(1)), set()).add(m.group(2))
    return out


def _expect_tags(target: str) -> dict[int, str]:
    """Parse `# EXPECT[<code>]` markers from a fixture file -> {line -> expected code}."""
    tags: dict[int, str] = {}
    for i, line in enumerate((ROOT / target).read_text().splitlines(), start=1):
        m = _EXPECT_RE.search(line)
        if m:
            tags[i] = m.group(1)
    return tags


@pytest.fixture
def mypy_errors() -> Callable[[str], dict[int, set[str]]]:
    return _run_mypy_strict


@pytest.fixture
def expect_tags() -> Callable[[str], dict[int, str]]:
    return _expect_tags


@pytest.fixture
def clean_gate_ok() -> Callable[[], subprocess.CompletedProcess[str]]:
    def run() -> subprocess.CompletedProcess[str]:
        env = dict(os.environ, MYPYPATH=str(ROOT))
        return subprocess.run(
            [sys.executable, "-m", "mypy", "--config-file", "mypy.ini"],
            cwd=str(ROOT), env=env, capture_output=True, text=True,
        )

    return run
