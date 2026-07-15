#!/usr/bin/env python3
"""pytest conftest for the engine — puts engine/ on sys.path so engine/tests/*.py import their
sibling engine modules (acts_join, acts_edb, dto_authentic_verify, ledger_diff_scratch, …) by bare
name, exactly as they did when the whole surface was one flat fact-mining directory. Autoharn's
split (engine/ vs engine/tests/) makes the bridge explicit; this is the standard pytest idiom for a
package whose tests sit one level below its modules. Lazy imports banned."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
