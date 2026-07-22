#!/usr/bin/env python3
"""test_targets_deployment -- qualification gate for engine/targets.py's THIRD resolution source
(vestigial_documentation/design/ORCH-OPUS-READINESS.md move 1): a deployment.json read via LEDGER_DEPLOYMENT, and the
precedence rule (explicit registry > deployment file > LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN env
vars) `targets.py`'s docstring states and justifies. DB-free (targets.resolve() never opens a
connection); no skip condition needed.

  * AC1 -- a name NOT in the registry resolves via LEDGER_DEPLOYMENT to the file's (db, schema, kern).
  * AC2 -- a name IN the registry still resolves to the registry entry even with LEDGER_DEPLOYMENT
    set to a DIFFERENT record (registry outranks the deployment file -- the precedence this test
    exists to pin).
  * AC3 -- a deployment file outranks the bare LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN env vars when
    both are set for an unregistered name.
  * AC4 -- a missing/malformed deployment file raises `deployment_record.DeploymentError` loudly
    (never silently falls through to the next source).
  * AC5 -- with no LEDGER_DEPLOYMENT set, an unregistered, non-scratch name still refuses exactly
    as before this module's move-1 change (no regression to the base refusal).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import targets
from deployment_record import DeploymentError


def _write(tmp_path: Path, **fields) -> Path:
    p = tmp_path / "deployment.json"
    p.write_text(json.dumps(fields), encoding="utf-8")
    return p


def test_deployment_file_resolves_unregistered_name(tmp_path, monkeypatch):
    dep = _write(tmp_path, db="depdb", host="10.0.0.9", schema="depschema", kern="depkern", role="deprw")
    monkeypatch.setenv("LEDGER_DEPLOYMENT", str(dep))
    ti = targets.resolve("some-scaffolded-project-name")
    assert ti == targets.TargetInfo(db="depdb", schema="depschema", kern="depkern")


def test_registry_outranks_deployment_file(tmp_path, monkeypatch):
    dep = _write(tmp_path, db="wrongdb", host="x", schema="wrongschema", kern="wrongkern", role="x")
    monkeypatch.setenv("LEDGER_DEPLOYMENT", str(dep))
    assert targets.resolve("toy") == targets.TargetInfo(db="toy", schema="toycolors", kern="toycolors_kernel")


def test_deployment_file_outranks_bare_env_vars(tmp_path, monkeypatch):
    dep = _write(tmp_path, db="depdb", host="h", schema="depschema", kern="depkern", role="r")
    monkeypatch.setenv("LEDGER_DEPLOYMENT", str(dep))
    monkeypatch.setenv("LEDGER_DB", "envdb")
    monkeypatch.setenv("LEDGER_SCHEMA", "envschema")
    monkeypatch.setenv("LEDGER_KERN", "envkern")
    ti = targets.resolve("some-scaffolded-project-name")
    assert ti == targets.TargetInfo(db="depdb", schema="depschema", kern="depkern")


def test_malformed_deployment_file_refuses_loudly(tmp_path, monkeypatch):
    dep = tmp_path / "deployment.json"
    dep.write_text("not json", encoding="utf-8")
    monkeypatch.setenv("LEDGER_DEPLOYMENT", str(dep))
    with pytest.raises(DeploymentError):
        targets.resolve("anything")


def test_missing_deployment_file_refuses_loudly(tmp_path, monkeypatch):
    monkeypatch.setenv("LEDGER_DEPLOYMENT", str(tmp_path / "does-not-exist.json"))
    with pytest.raises(DeploymentError):
        targets.resolve("anything")


def test_no_deployment_no_regression_to_base_refusal(monkeypatch):
    monkeypatch.delenv("LEDGER_DEPLOYMENT", raising=False)
    monkeypatch.delenv("LEDGER_DB", raising=False)
    monkeypatch.delenv("LEDGER_SCHEMA", raising=False)
    monkeypatch.delenv("LEDGER_KERN", raising=False)
    with pytest.raises(ValueError, match="unknown ledger target"):
        targets.resolve("nonexistent-xyz")
