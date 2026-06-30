#!/usr/bin/env python
"""impedance.lib — the per-library adapter singletons. Adding a library is adding ONE file here.

Each adapter imports exactly its own numerical library, lazily — so a consumer pays only for the
adapters it touches. The singletons are pure interpreter objects (no mutable state); import them
under natural library-handle names:

    from impedance.lib import torch, numpy as host, jax, jax_lower, scipy
"""

from __future__ import annotations

from impedance.lib.jax_lib import jax
from impedance.lib.jax_lower_lib import jax_lower
from impedance.lib.numpy_lib import numpy
from impedance.lib.scipy_lib import scipy
from impedance.lib.torch_lib import torch

__all__ = ["torch", "numpy", "jax", "jax_lower", "scipy"]
