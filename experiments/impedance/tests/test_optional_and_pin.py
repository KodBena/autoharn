#!/usr/bin/env python
"""tests/test_optional_and_pin.py — the optional 5th adapter, and the jax/jaxlib pin guard.

  * the OPTIONAL sklearn adapter (added as ONE file, host-family over numpy carriers) works and is
    skipped cleanly if scikit-learn is absent — the demo never depends on it, so the jax pin is
    never at risk from it;
  * jax/jaxlib stay pinned at 0.10.1 (verified after any optional install — DESIGN.md §6).
"""

from __future__ import annotations

import numpy as np
import pytest


def test_jax_jaxlib_pinned_0_10_1() -> None:
    import jax
    import jaxlib
    assert jax.__version__ == "0.10.1", f"jax pin drifted: {jax.__version__}"
    assert jaxlib.__version__ == "0.10.1", f"jaxlib pin drifted: {jaxlib.__version__}"


def test_sklearn_optional_adapter_is_host_family() -> None:
    pytest.importorskip("sklearn")
    from impedance.dtype import F32
    from impedance.lib import numpy as host
    from impedance.lib.sklearn_lib import sklearn

    a = host.brand(np.array([[3.0, 4.0], [1.0, 0.0]], dtype=np.float32), dev=host.HOST_DEVICE, dt=F32)
    out = sklearn.l2_normalize(a, axis=1)
    rows = np.asarray(host.unwrap(out))
    assert np.allclose(np.linalg.norm(rows[0]), 1.0)  # [3,4] -> unit norm
    assert rows.dtype == np.float32
