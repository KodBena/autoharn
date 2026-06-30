#!/usr/bin/env python
"""nla_lab.lower.dtype — phantom dtype tags for the lowerable kernel algebra carrier.

These classes are NEVER instantiated. They exist only as the phantom type parameter `D`
of `Tile[D]` (see `lower/tile.py`): `Tile[F32]` is a float32 register-tile, `Tile[I32]` an
int32 index tile, `Tile[BoolT]` a predicate tile. They make the dtype SEAM type-closed —
the band/select/clip index machinery is typed `Tile[I32]`, the score math `Tile[F32]`, and
the ONLY way to cross between them is the explicit `to_i32`/`to_f32` combinator in `ops.py`
(`Tile` exposes no `.astype`). A silent `float->int` coercion — the smell flagged from
`make_log_bucket_position`'s `log`/`ceil` — is therefore unconstructable: it must be written
as a diff-visible, single-home `to_i32(...)`.

HOST-XOR-DEVICE. Pure-python marker classes; imports neither numpy nor a device lib.
"""

from __future__ import annotations


class DType:
    """Phantom base — the type-level dtype tag. Never instantiated."""
    __slots__ = ()

    def __init__(self) -> None:  # pragma: no cover - phantom, never constructed
        raise TypeError("DType tags are phantom type parameters; they are never instantiated.")


class F32(DType):
    """Phantom tag: a float32 register-tile element dtype."""
    __slots__ = ()


class I32(DType):
    """Phantom tag: an int32 index/position element dtype."""
    __slots__ = ()


class BoolT(DType):
    """Phantom tag: a boolean predicate element dtype."""
    __slots__ = ()
