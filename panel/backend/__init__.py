# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:20:17Z
#   last-change: 2026-07-14T23:20:17Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend — the maintainer co-sign panel's FastAPI service (WP-A).

See panel/README.md for the operator walkthrough and BUILD-SPEC.md (design/ history) for the
full architect spec this package implements (API contract in spec S3). This package is a pure
consumer of the existing ledger surfaces: it reads via SELECTs over `filing/deployment_record.py`
+ `instruments/pghost_resolve.py`-resolved connections, and writes ONLY by shelling to the
repo-root `./led` verb (panel/backend/cosign.py) -- never a parallel write path.
"""
from __future__ import annotations
