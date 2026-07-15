#!/usr/bin/env bash
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T20:00:50Z
#   last-change: 2026-07-10T20:00:50Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

set -euo pipefail
python3 -c "import os; print(os.urandom(32).hex())" > stamp_secret.hex
chmod 600 stamp_secret.hex
