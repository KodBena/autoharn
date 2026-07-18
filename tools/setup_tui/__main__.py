# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:34:33Z
#   last-change: 2026-07-18T21:34:33Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""`python3 -m tools.setup_tui` -- thin redirect to `tools/setup_tui/app.py`'s `main`."""
from __future__ import annotations

from tools.setup_tui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
