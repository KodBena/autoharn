#!/usr/bin/env python
"""nla_lab — the modular inference interface + auto-benchmark harness for a portfolio
of NLA acceleration techniques against the DeBERTa-encoder + Maverick-coref stack.

See DESIGN.md (next to this file) for the full design: the typed `EncodeVariant`
contract, the registry, the auto-bench runner (latency + throughput + P6 fidelity vs
the exact reference), the exact-reference wrapping, the <=8 portfolio stubs, the
host-XOR-device file layout, and the gate updates.

Run the harness self-proof:  python -m nla_lab.bench --self-test
"""

from __future__ import annotations
