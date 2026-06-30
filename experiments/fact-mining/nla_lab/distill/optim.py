#!/usr/bin/env python
"""distill.optim — the DEVICE-side optimizer (optax AdamW baseline).

BASELINE: optax AdamW (`optax==0.2.8`, `jax==0.10.1` — verified importable in the
generic venv). AdamW is the safe, known-good baseline for STE gradients; it ships
first. The shadow Linear weights are a flat dict pytree; optax operates over it
directly.

ASPIRATION (NOT the baseline): Muon / Newton-Schulz (NLA-OPTIMIZATION-PORTFOLIO.md §8).
The shadow Linear weights are exactly the 2-D matrices Muon's orthogonalizing update
targets; the Newton-Schulz coupled iteration sidesteps eigendecomposition. Minted as a
second transform ONLY if a measured AdamW run motivates it (ADR-0011: mechanism on the
second occurrence, not speculatively). Noted here, not built.

HOST-XOR-DEVICE: imports `jax` + `optax`. `optax` is gate-neutral (not numpy, not a
name-flagged device lib), and the file also `import jax`, so its AST is a single side
(device-only) — XOR-clean. Neutral filename. NEVER numpy.
"""

from __future__ import annotations

import jax
import optax


def make_adamw(lr: float, weight_decay: float = 0.0,
               b1: float = 0.9, b2: float = 0.999) -> optax.GradientTransformation:
    """The baseline optimizer over the shadow pytree. `weight_decay=0.0` by default: the
    student is initialized AT the teacher weights, so decaying them toward zero would
    pull the student away from the teacher manifold the distillation targets — decay is a
    deliberate, opt-in knob, not the default."""
    return optax.adamw(learning_rate=lr, weight_decay=weight_decay, b1=b1, b2=b2)


def init_state(opt: optax.GradientTransformation,
               trainable: dict[str, jax.Array]) -> optax.OptState:
    """Initialize the optimizer state over the trainable pytree (the Linear shadows)."""
    return opt.init(trainable)
