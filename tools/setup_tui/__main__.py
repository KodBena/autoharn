"""`python3 -m tools.setup_tui` -- thin redirect to `tools/setup_tui/app.py`'s `main`."""
from __future__ import annotations

from tools.setup_tui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
