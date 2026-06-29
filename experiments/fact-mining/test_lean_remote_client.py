#!/usr/bin/env python
"""THE FORECLOSING GATE (ADR-0011 Rule 2 / ADR-0000): the --remote client is lean.

THE LARD this forecloses (measured this session): the old --remote client paid a
cold ML-stack import on every invocation — `import spacy` drags thinc -> torch
(~1.06s on the guest, ~0.65s torch + ~1.2s transformers + ~2.1s spaCy/thinc cold on
the host stack, ~4.4s total) purely to deserialize a DocBin and walk a Doc, even
though the daemon already did the GPU work. A client that imports only json + zmq +
psycopg costs ~0.18s. There is NO "lean spaCy" import — `from spacy.tokens import
DocBin` alone still pulls torch unconditionally (spaCy's __init__ imports
thinc -> torch). So the only fix is structural: the client STOPS importing spaCy on
the remote path at all — the daemon runs the SSOT extractor (extract.doc_to_facts)
host-side and ships JSON facts.

This gate quantifies over the CLASS, not the instance (ADR-0011 Rule 4): it fails if
`import load_facts` + building the remote client (RemoteNLP) + constructing a facts
request + building the remote --cache wrapper (nlp_cache.FactCache / CachingFacts)
pulls ANY of torch / spaCy / transformers / thinc into sys.modules. Driving the cache
sub-path matters: nlp_cache is lazy-imported only on `--remote --cache`, so a
module-scope `import spacy` added to nlp_cache.py would NOT be caught by a probe that
stops at RemoteNLP (the error message named nlp_cache, but the no-cache probe never
traversed it — that coverage gap is now closed). A future edit that re-adds a
module-scope `import spacy` to extract.py / nlp_client.py / nlp_cache.py, or routes
the remote path back through a DocBin, trips this RED — the lard cannot silently
return.

It runs each probe in a FRESH interpreter (subprocess) because pytest itself, or a
sibling test, may already have imported spaCy into THIS process's sys.modules — an
in-process check would be vacuously green. The negative self-check
(test_gate_is_nonvacuous) proves the gate has teeth: the identical probe with a
deliberate `import spacy` appended is CAUGHT.

Run under pytest, or standalone: `python test_lean_remote_client.py`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The ML stack the lean remote client must never pull (by top-level module name).
HEAVY = {"torch", "spacy", "transformers", "thinc"}

# Drive the remote codepath far enough to BUILD the client and a facts request,
# WITHOUT a live daemon (zmq connect() is lazy/non-blocking — it needs no peer). Then
# report which heavy modules got imported, as JSON on the last stdout line.
#
# This drives the WHOLE remote class, not one instance (ADR-0011 Rule 4): both the
# plain `--remote` sub-path (RemoteNLP + facts request) AND the `--remote --cache`
# sub-path (nlp_cache -> FactCache -> CachingFacts) are exercised. The cache wrapper is
# constructed DIRECTLY rather than through extract.build_nlp because build_nlp calls
# nlp.info(), which needs a live daemon; FactCache/CachingFacts is the construction
# build_nlp would do, and it must stay spaCy-free too (FactCache is json+redis only,
# redis.from_url is lazy so no live redis is needed).
_PROBE = r"""
import sys, json
import load_facts                          # the lean client module
from nlp_client import RemoteNLP
nlp = RemoteNLP("tcp://127.0.0.1:5599")    # construct the remote client (no daemon needed)
req = nlp._req(["a sentence to parse"], "facts")   # drive facts-request construction
assert req["format"] == "facts" and req["op"] == "parse"
import nlp_cache                           # the --remote --cache sub-path of the class
from nlp_cache import FactCache, CachingFacts
fc = FactCache("en_core_web_sm", url="redis://127.0.0.1:6380/0")  # json+redis, no daemon/redis needed
cached = CachingFacts(nlp, fc)             # the lean facts cache wrapper build_nlp builds
heavy = sorted(m for m in sys.modules if m.split(".")[0] in %r)
print(json.dumps(heavy))
""" % (HEAVY,)


def _heavy_modules_after(probe: str) -> list[str]:
    """Run `probe` in a fresh interpreter; return the heavy modules it imported."""
    r = subprocess.run([sys.executable, "-c", probe], cwd=HERE,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (
        f"probe subprocess failed (rc={r.returncode}):\n{r.stdout}\n{r.stderr}")
    return json.loads(r.stdout.strip().splitlines()[-1])


# ===================================================================== the gate
def test_remote_client_imports_no_ml_stack():
    """`import load_facts` + build RemoteNLP + build a facts request + build the
    --remote --cache wrapper (FactCache / CachingFacts) pulls NONE of torch / spaCy /
    transformers / thinc. The lard is foreclosed structurally across the whole class."""
    heavy = _heavy_modules_after(_PROBE)
    assert heavy == [], (
        "THE LARD RETURNED: the --remote client pulled the ML stack "
        f"{heavy} — a module-scope `import spacy` (in extract.py / nlp_client.py / "
        "nlp_cache.py) or a DocBin on the remote path is back. The remote path must "
        "import only json + zmq + psycopg; the daemon runs extract.doc_to_facts "
        "host-side and ships JSON facts.")


# ============================================================ negative self-check
def test_gate_is_nonvacuous():
    """The gate is not vacuously green: the SAME probe with a deliberate `import
    spacy` PREPENDED is CAUGHT (proving the detector actually sees the ML stack and
    the green result above is real, not a blind spot). It must be prepended, not
    appended — the probe snapshots sys.modules then prints, so a trailing import
    would land after the measurement and prove nothing."""
    heavy = _heavy_modules_after("import spacy\n" + _PROBE)
    assert "spacy" in heavy, (
        "non-vacuity FAILED: a deliberate `import spacy` was NOT detected — the gate "
        "is blind and its green result is meaningless")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
