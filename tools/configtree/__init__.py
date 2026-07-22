#!/usr/bin/env python3
"""tools/configtree -- a generic hierarchical-configuration-editor library
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2/§6): a sidebar Tree of every configuration section
(status complete/incomplete/invalid/blocked-with-reason), a form pane, dependency-as-data
blocking, and a commit node, with ZERO knowledge of any particular consumer. `tools/setup_tui/`
is the one consumer today; nothing in this package imports from `tools.setup_tui` (enforced by
`gates/setup_tui_purity_gate.py`'s one-way-dependency check) -- a new consumer adds itself by
importing this package and handing it `SectionSpec`/`CommitSpec` instances, never by editing it.

DELIBERATELY does NOT re-export `ConfigTreeApp` here: `tools.configtree.app` (and
`tools.configtree.widgets`) are the only modules in this package that import `textual` --
`tools.setup_tui.steps`/`steps_*.py` need `SectionSpec`/`TextField`/etc. (this module's own
exports) to declare their section data WITHOUT paying textual's import cost, which is exactly
what `--from-config`'s "zero Textual involved" headless path depends on. A consumer that needs
the live App imports it explicitly: `from tools.configtree.app import ConfigTreeApp`."""
from __future__ import annotations

from tools.configtree.fields import (ChoiceField, ConfirmField, DescriptionElement,
                                      ElucidationHeading, ElucidationItem, ElucidationValue,
                                      Field, ListField, MultiChoiceField, PROVENANCE_LABEL,
                                      TextField, default_of, get_field_value, is_field_touched,
                                      set_field_value, validate_value)
from tools.configtree.ids import ExitCode, FieldName, Label, NodeId, ScopedFieldKey
from tools.configtree.spec import (BLOCKED, COMPLETE, INCOMPLETE, INVALID, ActionSpec, CommitSpec,
                                    DuplicatedSharedFieldError, SectionResult, SectionSpec,
                                    all_sections_complete, owner_of, ready_for_commit,
                                    section_answers, section_field_errors, section_status,
                                    validate_shared_ownership)

__all__ = [
    "ChoiceField", "ConfirmField", "DescriptionElement", "ElucidationHeading", "ElucidationItem",
    "ElucidationValue", "Field", "ListField", "MultiChoiceField", "PROVENANCE_LABEL", "TextField",
    "default_of", "get_field_value", "is_field_touched", "set_field_value", "validate_value",
    "ExitCode", "FieldName", "Label", "NodeId", "ScopedFieldKey",
    "BLOCKED", "COMPLETE", "INCOMPLETE", "INVALID",
    "ActionSpec", "CommitSpec", "DuplicatedSharedFieldError", "SectionResult", "SectionSpec",
    "all_sections_complete", "owner_of", "ready_for_commit", "section_answers",
    "section_field_errors", "section_status", "validate_shared_ownership",
]
