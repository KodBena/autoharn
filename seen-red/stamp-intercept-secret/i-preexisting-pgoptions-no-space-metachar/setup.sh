#!/usr/bin/env bash
set -euo pipefail
python3 -c "import os; print(os.urandom(32).hex())" > stamp_secret.hex
chmod 600 stamp_secret.hex
