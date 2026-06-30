#!/usr/bin/env python
"""nla_lab — the guest-checkable ACL for the Pallas-Triton LOWERING CAPABILITY (the 'lib' axis).

Each entry is a MEASURED sm_75 host wall turned into a jaxpr-level predicate, so the whole
"unsupported primitive" class dies on the CPU laptop instead of on the 2080Ti after a compile +
a psql round-trip. The walls so far, each of which cost a host round-trip to discover:
  - `gather` — "Unimplemented primitive in Pallas Triton lowering: gather" (the c2p/p2c
    relative-position select, AND the idx1d bucket-table read — both since retired for a pl.ds
    band + arithmetic bucket).
  - batched `dot_general` — `_dot_general_lowering` asserts `batch_dims == ((), ())`; a `jnp.einsum`
    that shares an index across both operands AND the output (e.g. "iw,ijw->ij") lowers to a
    BATCHED matmul that Pallas-Triton refuses (retired for broadcast-multiply + sum).

SCOPE (honest, ADR-0009): audits ONLY the body of each `pallas_call` — that is what gets
Triton-lowered; the surrounding dense graph runs on XLA, where gather/batched-matmul are fine.
And it covers ONLY the jaxpr-VISIBLE walls: an unsupported PRIMITIVE is present in the jaxpr
BEFORE the GPU lowering. QUANTITATIVE/lowering-internal walls — SMEM bytes (the `smem_bytes`
gate), the sm_75 carveout grant, whether `jnp.log`/`jnp.ceil` lower — are NOT jaxpr-visible and
remain the `smem_bytes` gate + the host run. This is the 'lib-primitive' slice of the
(device, lib, dtype, shape) capability ACL, ACCUMULATED from measurement — never claimed a priori
(claiming a complete Triton-capability model would be the unsubstantiated empirical claim to avoid).

HOST-XOR-DEVICE: this is jaxpr ANALYSIS — `jax.make_jaxpr` is abstract eval, no device op runs —
a guest tool; it authors no device computation.
"""
from __future__ import annotations

from typing import Any, Iterator

import jax


def _as_jaxpr(obj: Any) -> Any:
    """A `Jaxpr` (has `.eqns`) or the inner jaxpr of a `ClosedJaxpr` (has `.jaxpr`), else None.
    Duck-typed so it survives jax's `jax.core` -> `jax.extend.core` churn (these types are
    unstubbed, so isinstance would couple us to a moving import path)."""
    if hasattr(obj, "eqns"):
        return obj
    inner = getattr(obj, "jaxpr", None)
    if inner is not None and hasattr(inner, "eqns"):
        return inner
    return None


def _subjaxprs(eqn: Any) -> Iterator[Any]:
    """Every sub-jaxpr nested in an eqn's params (scan/cond/while/pallas_call bodies, etc.)."""
    for val in eqn.params.values():
        for item in (val if isinstance(val, (tuple, list)) else (val,)):
            sub = _as_jaxpr(item)
            if sub is not None:
                yield sub


def _is_batched_dot(eqn: Any) -> bool:
    """A `dot_general` whose `dimension_numbers` carry batch dims — the form Pallas-Triton
    rejects (`assert batch_dims == ((), ())`)."""
    (_, (lhs_batch, rhs_batch)) = eqn.params["dimension_numbers"]
    return bool(lhs_batch) or bool(rhs_batch)


def triton_kernel_violations(closed_jaxpr: Any) -> list[str]:
    """Walk `closed_jaxpr` and return the Pallas-Triton lowering violations found INSIDE any
    `pallas_call` body (the surrounding XLA graph is NOT audited). Empty list == the kernel is
    jaxpr-clean of the measured primitive walls."""
    out: list[str] = []

    def visit(jaxpr: Any, inside_kernel: bool) -> None:
        for eqn in jaxpr.eqns:
            name = eqn.primitive.name
            if inside_kernel:
                if name == "gather":
                    out.append("gather: Pallas-Triton has no gather lowering "
                               "(use a pl.ds band slice + one-hot select)")
                elif name == "dot_general" and _is_batched_dot(eqn):
                    out.append("batched dot_general: Pallas-Triton asserts batch_dims==((),()) "
                               "(a shared-index einsum -> use broadcast-multiply + sum)")
            for sub in _subjaxprs(eqn):
                visit(sub, inside_kernel or name == "pallas_call")

    visit(closed_jaxpr.jaxpr, False)
    return out


def assert_triton_lowerable(fn: Any, *args: Any, **kwargs: Any) -> None:
    """Trace `fn` to a jaxpr (CPU abstract eval — NO GPU) and raise if any `pallas_call` body
    contains a measured Pallas-Triton wall. The guest gate that turns each host "Unimplemented
    primitive" / lowering assert into a laptop failure, before the 2080Ti is ever touched."""
    cj = jax.make_jaxpr(fn)(*args, **kwargs)
    viol = triton_kernel_violations(cj)
    if viol:
        raise AssertionError(
            "pallas_call body is NOT Pallas-Triton lowerable on sm_75:\n  - " + "\n  - ".join(viol))
