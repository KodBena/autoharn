# `nla_lab/lower` — the lowerable kernel algebra (settled design)

Status: **SETTLED + FOUNDATION-HARDENED.** This document is an adjudication, not an
options menu. It was commissioned as a fresh, decisive ruling after the collaborators
went back and forth on the vehicle. It decides ONE design and is implemented verbatim.

> **Revision (post-implementation adversarial critique, ADR-0009 honesty).** The first
> implementation shipped a *holed foundation*: (CRITICAL-1) the carrier's construction
> token `_PRIV` was an importable module global, so `from …tile import _PRIV` minted a
> dtype-LYING `Tile` mypy-clean — defeating lib+dtype+the einsum backstop in one line;
> (HIGH-2) registering `Tile` as a jax pytree let `tree_map` rewrap an arbitrary op's
> result back into a valid `Tile`; (HIGH-3) the device seam was only operand-checking
> relabeled, with the genuine host↔device residence never in the types. All three are now
> fixed in the carrier itself: the carrier is **non-constructable** (raising `__init__`,
> mint only via package-private `object.__new__`, **no importable token**); it is **not a
> pytree** (an opaque leaf; the `fori_loop` carry moved into `ops.fold_kt`, wrap/unwrap
> inside `lower/`); and the device boundary takes a **`Ref` brand** (§4.device). §4 below
> carries the honest per-axis closure split (type-closed / construction-time / host-only).

Authored against ADR-0000 (illegal states unrepresentable — the four impedances must be
*unconstructable*, not lint-detected), ADR-0012 P1/P8 (one SSOT; the typed signature is
the contract), ADR-0009 (MEASURED; honest about type-closable vs host-only), ADR-0013
(no de-scope; the full four-seam surface is owed). The proving ground is
`nla_lab/variants/_pallas_disent_attention.py`; the fidelity oracle is
`nla_lab/variants/exact_reference.py` via `jax_deberta`.

---

## 0. The criterion, restated as the bar this design is judged against

Four seam axes have reached the 2080Ti host before we caught them. Each must be encoded
so a mismatch is **unconstructable** — a mypy error or a non-existent constructor — in
**one** composable SSOT:

- **lib** — a non-Pallas/Triton-lowerable op in a kernel (`gather`; a batched
  `dot_general` from a shared-index einsum) → measured host wall.
- **device** — host code touching device data or vice versa → must live in the types, not
  only a file-level AST lint. Closed in TWO type sub-axes (value-flow: `Tile` vs host
  scalar; residence boundary: a `Ref` brand on every kernel load/store) + the file gate
  for the import-graph class (§4.device).
- **dtype** — a silent `float→int` coercion (from `log`/`ceil`) fine on CPU jax, wrong on
  Triton → must be explicit/typed, never silent.
- **shape** — a non-power-of-2 kernel dim (the 2S−1 trap) → `Pow2` already closes *some*
  dims; this is the model to generalize.

**The firm constraint:** fusion is XLA's job, lowering is Pallas's job. We build a
**correctness/type layer only.** The emit-Triton / `triton.compile` / `jax.ffi` path is
SCRAPPED. We constrain our *input* to the stack so only lowerable ops are constructible;
the resulting jaxpr is handed to `pl.pallas_call`, which Pallas/XLA lower and fuse. We
never reach past the stack and we never reimplement optimization.

---

## 1. The nomenclature ruling (the maintainer's "algebra" / "F-algebra", fixed)

The maintainer's instinct — reach for an *algebra* — is **correct**. The precise
nomenclature is not. The ruling, decisively:

1. **It IS an algebra** in the universal-algebra sense: a **carrier** (an opaque device
   register-tile type) plus a **signature of operations** (the combinator surface). The
   word "algebra" the maintainer reached for is the glue/eDSL sense and it is right.

2. **It is NOT an initial F-algebra with a catamorphic `fold` over a reified AST.** That
   pattern builds a term first (which CAN be built wrong — a `Gather` node is a perfectly
   good value) and rejects the bad term only when the `fold` walks it. **That is exactly
   the shape the maintainer already REJECTED:** the runtime jaxpr-walk in
   `nla_lab/variants/_triton_acl.py` is a catamorphism over the jaxpr-as-initial-algebra
   that flags `gather`/batched-`dot_general` *at fold time*. The rejection — "it is not an
   ACL if its semantics do not live in the type system" — is precisely the rejection of
   initial-style. We do not relitigate it; we honor it.

3. **It IS a tagless-final (final-style) typed-combinator embedded DSL with a single
   opaque carrier and smart constructors.** Equivalently: a typed Σ-algebra realized in
   final style. In final style the operations are **typed combinators**; an ill-formed
   kernel is an **ill-typed expression** — there is no reified term to fold and therefore
   no fold-time check to reject. The seam-closure is a property of the combinator
   **signatures**, evaluated by mypy at construction. *This is why final-style strictly
   beats initial-style for this criterion:* the criterion literally is "a mismatch is a
   mypy error / a non-existent constructor," which is the definitional property of a
   tagless-final embedding.

4. **The "fold to lowerable primitives" is degenerate and singular.** There is exactly
   one interpretation: the carrier is a private newtype over `jax.Array`, and each
   combinator's body is the lowerable `jnp`/`pl` expression already proven in the
   kernel. "Folding" is just eager interpretation as each combinator is called — there is
   no separate catamorphism because there is no separate term. (Final style *admits* a
   second interpretation — e.g. an abstract SMEM/shape cost — by parameterizing over a
   `Repr` Protocol; we note this is available and do **not** build it. One carrier closes
   the four seams; a second is not owed by the criterion. ADR-0013: not a de-scope — a
   second interpreter forecloses no impedance class, so it earns no place; ADR-0000's
   over-typing caveat.)

Call it, in code and prose, **the lowerable kernel algebra**: carrier `Tile`, surface
`ops`, shape SSOT `Pow2`.

---

## 2. The carrier types (the SSOT)

Package layout (one home per concern, P1/P3):

```
nla_lab/lower/
  __init__.py      # re-exports the public surface (Tile, Idx, Pow2, ops)
  shape.py         # Pow2 / pow2() / next_pow2  — the shape SSOT (moved here from the kernel)
  dtype.py         # F32 / I32 / BoolT phantom dtype tags
  tile.py          # the opaque carrier Tile[D] (+ Idx alias) — non-coercible, no public ops
  ops.py           # THE combinator surface — every Triton-lowerable op, and ONLY those
  DESIGN.md        # this file
```

### 2.1 Phantom dtype tags (`dtype.py`)

```python
class DType: ...           # never instantiated; phantom only
class F32(DType): ...
class I32(DType): ...
class BoolT(DType): ...
```

### 2.2 The opaque carrier (`tile.py`)

```python
from typing import Any, Generic, NewType, TypeVar, final
import jax
from nla_lab.lower.dtype import DType, F32, I32

D = TypeVar("D", bound=DType)

Ref = NewType("Ref", jax.Array)          # a device memory ref (the device-seam boundary brand)

@final
class Tile(Generic[D]):
    """An opaque device register-tile, phantom-typed by its element dtype D.

    DELIBERATELY non-ArrayLike and NON-COERCIBLE: it defines NO __array__,
    NO __jax_array__, NO __array_namespace__, NO arithmetic dunders, and NO
    __getitem__. Two consequences, which are the whole design:

      (a) mypy rejects a Tile anywhere an ArrayLike/array is expected (it is not
          ArrayLike), so a raw fancy-index a[idx] (the gather) or jnp.sum(tile)
          does not type-check; and
      (b) at TRACE/construction time, feeding a Tile to ANY un-wrapped jnp/lax
          primitive raises (jax cannot convert a non-coercible object to an
          array) — the construction-time backstop that closes the ONE residual
          mypy cannot (jnp.einsum's Any-typed *operands; see §4.lib).

    NON-CONSTRUCTABLE (hardened, CRITICAL-1). There is NO public constructor and
    NO importable construction token: __init__ unconditionally RAISES, so Tile(...)
    is a runtime error AND a mypy [call-arg] error (no value params). The package
    mints a Tile ONLY through _wrap (below), via object.__new__, which bypasses
    __init__ — a path a caller cannot name. (The earlier _PRIV single-underscore
    module token was importable, which let a caller mint a dtype-LYING Tile
    mypy-clean; that token is GONE.)

    NOT A PYTREE (hardened, HIGH-2). Tile is deliberately NOT registered as a jax
    pytree: registration made tree_map(f, tile) reach the backing array and REWRAP
    an arbitrary (gather/coerced) result into a valid Tile — a mypy-invisible
    re-entry vector. Unregistered, a Tile is an opaque LEAF; the running (m,l,acc)
    state crosses fori_loop via ops.fold_kt, which keeps wrap/unwrap inside lower/."""
    __slots__ = ("_arr",)
    _arr: jax.Array
    def __init__(self) -> None:
        raise TypeError("Tile is package-private and NON-CONSTRUCTABLE outside lower/.")

def _wrap(arr: jax.Array) -> "Tile[Any]":   # the ONE mint path; package-private, no token
    t: Tile[Any] = object.__new__(Tile)
    t._arr = arr
    return t

Idx = Tile[I32]                          # an integer index/position tile
```

`Tile` is the single carrier for **all four** seams: it is the *device* brand (device
XOR host lives in `Tile` vs plain `int`/`float`), it is the *lib* surface (its only
operations are the lowerable combinators), it is *dtype*-typed by `D`, and its
shape-fixing constructors take *`Pow2`*. One SSOT, four seams.

### 2.3 The shape SSOT (`shape.py`)

`Pow2`, `pow2()`, `next_pow2()` **move here verbatim** from
`_pallas_disent_attention.py` (P1: one home; the kernel imports them from `lower.shape`).
They are unchanged — the existing, working shape ACL — now the SSOT the whole algebra
shares rather than one kernel's local helper.

---

## 3. The combinator surface (`ops.py`)

Every function takes and returns `Tile` (or `Pow2`/host scalars), and **its body is the
exact lowerable `jnp`/`pl` expression already proven in `disent_flash_kernel`.** The
surface is *closed*: it contains every Triton-lowerable op the disentangled-flash kernel
needs, and **nothing else** — no `gather`, no `take`, no `einsum`, no `dot_general` with
batch dims, no `astype`. Signatures (bodies elided; each is one line of the existing
kernel, wrapped `unwrap → jnp/pl call → _wrap(_)`):

```python
# ---- constructors (every shape-fixing dim is Pow2 — the shape seam) -----------
def zeros(rows: Pow2, cols: Pow2, dtype: type[D]) -> Tile[D]: ...
def full(rows: Pow2, value: float) -> Tile[F32]: ...          # e.g. running max = -inf
def iota(n: Pow2) -> Idx: ...                                  # jnp.arange(n)
def ref(x: jax.Array) -> Ref: ...                             # the ONE host-array -> device-ref brand
def load(r: Ref, *dims: Pow2) -> Tile[F32]: ...               # r[...] at the kernel boundary (Ref, not raw Array)

# ---- elementwise arithmetic (lowerable) ---------------------------------------
def add(a: Tile[D], b: Tile[D]) -> Tile[D]: ...
def sub(a: Tile[D], b: Tile[D]) -> Tile[D]: ...
def mul(a: Tile[D], b: Tile[D]) -> Tile[D]: ...                # broadcasting allowed (interpret-checked)
def mul_scalar(a: Tile[D], s: float) -> Tile[D]: ...
def div_scalar(a: Tile[D], s: float) -> Tile[D]: ...

# ---- transcendental / index arithmetic ----------------------------------------
def exp(a: Tile[F32]) -> Tile[F32]: ...
def sign(a: Tile[F32]) -> Tile[F32]: ...
def abs_(a: Tile[F32]) -> Tile[F32]: ...
def clip(a: Tile[I32], lo: int, hi: int) -> Idx: ...
def log(a: Tile[F32]) -> Tile[F32]: ...     # HOST-UNVERIFIED LOWERING (sm_75) — see §4.dtype residual
def ceil(a: Tile[F32]) -> Tile[F32]: ...    # HOST-UNVERIFIED LOWERING (sm_75) — see §4.dtype residual

# ---- compare / select ---------------------------------------------------------
def gt(a: Tile[D], b: Tile[D]) -> Tile[BoolT]: ...
def eq(a: Tile[I32], b: Tile[I32]) -> Tile[BoolT]: ...
def where(c: Tile[BoolT], a: Tile[D], b: Tile[D]) -> Tile[D]: ...

# ---- reductions ---------------------------------------------------------------
def rmax(a: Tile[F32], axis: int) -> Tile[F32]: ...
def rsum(a: Tile[D], axis: int) -> Tile[D]: ...

# ---- the ONLY contraction: 2-D, batch-free (the lib seam) ---------------------
def transpose(a: Tile[D]) -> Tile[D]: ...
def dot(a: Tile[F32], b: Tile[F32]) -> Tile[F32]: ...          # pl.dot — 2-D, NO batch dims

# ---- the gather replacement: band slice + one-hot select (the lib seam) -------
def band(ref: jax.Array, bh: int, row0: Idx0, rows: Pow2, base: Idx0, width: Pow2) -> Tile[F32]: ...
def onehot(sel: Idx, width: Pow2) -> Tile[F32]: ...            # to_f32(eq(iota(W), sel)) — no gather
def select(band_: Tile[F32], onehot_: Tile[F32], axis: int) -> Tile[F32]: ...  # rsum(mul(...)) — NOT einsum

# ---- the EXPLICIT dtype casts (the dtype seam) — the ONLY float<->int home -----
def to_i32(x: Tile[F32]) -> Idx: ...                           # the ONLY F32 -> I32 in the whole package
def to_f32(x: Tile[I32]) -> Tile[F32]: ...                     # the ONLY I32 -> F32

# ---- the bucket index (reuses jax_deberta.make_log_bucket_position — P1) -------
def bucket_index(rel: Idx, *, position_buckets: int, max_relative_positions: int,
                 span: int, two_span: int) -> Idx: ...
#   body == _bucket_index today, but the float->int step is an EXPLICIT to_i32(...)
#   call visible in ops.py — the cast has ONE home, never a buried .astype.
```

`Idx0` is `Tile[I32]` constrained to a 0-d (scalar) device int (the clamped band base
`base = clip(b_lo, 0, two_span-W)`); modeled as `Idx` with a runtime 0-d check at the
`band` boundary (interpret-checked; rank is not phantom-typed — see §5 honesty).

There is **no** combinator that produces a `Tile` from an array index, a batched
contraction, an einsum, or an implicit cast. That omission is the lib/dtype closure.

---

## 4. How EACH seam is made unconstructable — with the honest closure surface

The decisive table. For each seam: the mechanism, and **honestly** whether it is
type-closed (mypy), construction-raise-closed (trace-time), or host-only (un-closable).

### lib — `gather` and batched `dot_general` → **type-closed + construction-raise**

- **`gather`** is closed at **two** surfaces. (a) *mypy:* `Tile` is non-ArrayLike and
  defines no `__getitem__`, so `a[idx]` (advanced index) and `jnp.take`/`jnp.sum(tile)`
  do not type-check; and there is no `gather`/`take` combinator to call. (b)
  *construction-raise backstop:* even if a caller imports raw `jnp` and writes
  `jnp.take(tile._arr, ...)`, `tile._arr` is package-private and the surface that returns
  a `Tile` is unreachable — the value cannot re-enter the algebra. **Fully
  unconstructable.** (The pl.ds band + one-hot `select` is the sanctioned replacement,
  already proven bit-identical to the gather.)

- **batched `dot_general`** is the residual the probe flagged: jax's stubs type
  `jnp.einsum(*operands)` as `Any`, so `jnp.einsum("iw,ijw->ij", a, b)` with `Tile`
  operands **slips mypy**. It is closed at the **construction** surface instead, honestly:
  (a) the surface offers only `dot` (2-D, batch-free) and `select`
  (broadcast-`mul`+`rsum`), so a batched contraction is **not expressible** through the
  algebra; and (b) the **non-coercible carrier** is the backstop the probe said einsum
  needs — `jnp.einsum(tile, ...)` calls `jnp.asarray` on the operand, `Tile` has no
  `__array__`/`__jax_array__`, so it **raises a `TypeError` at trace time** (on the CPU
  guest, at `make_jaxpr`/interpret, before any host). **So einsum is unconstructable —
  not in mypy (it slips), but at construction (the value cannot be built).** This is the
  precise honesty the criterion demands: gather is mypy-closed; batched-einsum is
  construction-raise-closed.

  *Coverage of the residual, defense-in-depth (a TEST, not the ACL):* the rejected
  jaxpr-walk `_triton_acl.py` is **demoted** from "the ACL" to a `pytest` regression that
  asserts the construction backstop actually fires — i.e. that a deliberate raw-`jnp`
  escape in a fixture kernel raises at trace and that the algebra's own kernels are
  jaxpr-clean of `gather`/batched-`dot_general`. It tests the carrier discipline; it is
  not the discipline. (ADR-0000 escape-hatch posture: the type is the law, the walk is a
  belt over the suspenders.)

### device — host code touching device data → **two type-closed sub-axes + the file gate**

Split into three genuinely different claims, stated separately so none is overclaimed
(this is the HIGH-2/HIGH-3 reconciliation — the earlier draft conflated only the first
sub-axis with "the device seam"):

- **value-flow (type-closed).** The carrier is the device brand. A combinator that needs a
  host static takes `int`/`float`/`Pow2`; one that needs a device value takes `Tile`. mypy
  rejects a host `int`/`ndarray` where a `Tile` is wanted (`add(t, 1)` is `[arg-type]`) and a
  `Tile` where a host static is wanted. The only host→device value crossings are the explicit
  `full`/`iota`/`*_scalar(s: float)` lifts — each named and greppable.
- **residence boundary (type-closed, boundary brand).** The kernel-boundary loaders/stores
  (`load`/`band`/`store`/`load_block*`) take a `Ref` (a `NewType` over `jax.Array`), NOT a raw
  `jax.Array`. So a host array cannot slide into a kernel load un-branded: that is a mypy
  `[arg-type]` error. The single host-array→device-ref crossing is the explicit `ops.ref(...)`
  brand (the device-seam analog of `to_i32`). HONEST: this is a boundary *assertion* ("this
  array is a device kernel ref"), not a residence *proof* — stock `jax.Array` carries no
  host/device residence tag to type, so a `Ref` brand is the strongest a type can make; the
  brand being explicit and single-home is what puts the seam *in the carrier SSOT* rather than
  purely in a file lint.
- **import graph (file gate, AST).** The file-level import-XOR gate (`test_import_xor.py`)
  is **kept** for the *larger* class the types cannot reach — a whole module importing both
  `numpy` and a device lib. The carrier+`Ref` close host↔device *within a kernel's value flow
  and at its load boundary* (type-level); the import gate closes it *at the module-import
  graph* (AST, coarse). Neither subsumes the other; both are owed (`lower/*` in `SCANNED`).

### dtype — silent `float→int` coercion → **type-closed (the coercion); host-only (the lowering)**

Split into two genuinely different claims, stated separately so neither is overclaimed:

- **The coercion is type-closed.** `Tile` is dtype-phantom-typed. Positions/indices are
  `Tile[I32]`; `make_log_bucket_position`'s `log`/`ceil` arithmetic produces `Tile[F32]`.
  The band/`select`/`clip` machinery requires `Tile[I32]`. The **only** `F32→I32` path in
  the entire package is the explicit `to_i32` combinator; `Tile` exposes no `.astype`. So
  a silent coercion is **unconstructable** — to turn a float tile into an index you must
  *write `to_i32(...)`*, a mypy-typed, diff-visible, single-home event. (The bucket's own
  internal cast is an explicit `to_i32` inside `ops.bucket_index`, not a buried `.astype`
  — the smell the maintainer flagged is gone at its source.)

- **The lowering is host-only and is NOT claimed.** Whether `jnp.log`/`jnp.ceil`
  themselves have an sm_75 Triton lowering rule is *not* a dtype property and *not*
  type-closable — it is a `lib`-axis host-unknown. The `log`/`ceil` combinators are in the
  surface (they are ordinary primitives, not `gather`/batched-`dot`), tagged
  `HOST-UNVERIFIED LOWERING`. The design is honest (ADR-0009): the cast seam is fully
  closed; the orthogonal "does the float op lower on Turing" is filed as the measured host
  gate, not asserted green here.

### shape — non-pow2 kernel dim (2S−1) → **type-closed + construction-raise on runtime values**

The existing `Pow2`, generalized from "block dims only" to **every shape-fixing combinator
parameter**: `zeros(rows: Pow2, cols: Pow2, …)`, `iota(n: Pow2)`, `band(…, width: Pow2)`,
and the kernel's `BlockSpec` dims. A raw `int` dimension is a **mypy error** (`Pow2` is a
distinct `NewType`; `pow2()` is its only source and it validates). The `2S−1` trap is
unconstructable two ways: `2S−1` cannot be branded `Pow2` (`pow2()` raises on a non-pow2
value — the **construction-raise** for a dim known only at runtime, e.g. config-derived
`S`), and a bare `int` cannot be passed where `Pow2` is required (**mypy**). **Fully
closed.** The `smem_bytes` arithmetic gate (pure-int, guest-provable) composes on top:
`Pow2` dims feed it, and an SMEM *overflow* is a caught construction-time error — though
whether sm_75 *grants* the 64 KiB carveout remains host-only (ADR-0009), unchanged.

### The closure theorem (the spine, stated once)

> A kernel body authored in this algebra is a pure function
> `(Tile…, Idx…, Pow2…, host-scalar…) -> Tile`. Because the carrier is non-ArrayLike and
> non-coercible, the **only** way to produce a `Tile` from `Tile`s is a combinator in
> `ops.py`; and **every** combinator's signature encodes the four seams (lowerable-only
> ops; `Tile` vs host scalar; dtype phantom + explicit `to_i32`/`to_f32`; `Pow2` dims).
> Therefore a kernel that (i) type-checks under `mypy --strict` AND (ii) traces without
> raising is — *by construction* — gather-free, batched-einsum-free, host-clean,
> dtype-explicit, and pow2-shaped. The illegal kernel is unconstructable: either mypy
> rejects it (wrong type / non-existent combinator) or the trace raises (a non-coercible
> brand fed to an un-wrapped primitive).

The single class the theorem **cannot** cover, named loudly: whether a *surface-legal*
primitive (`log`, `ceil`, the fp32 `pl.dot` FMA path, the carveout grant) actually lowers
and runs on sm_75 Turing. That is host-only, filed per ADR-0009, measured on the 2080Ti —
never asserted here.

---

## 5. Honest boundaries of the typing (what is NOT phantom-typed, and why that is right)

ADR-0009 honesty + ADR-0000's anti-over-typing caveat. The design closes the four *named*
impedances and deliberately stops there:

- **Full shape tuples are not phantom-typed.** Dimension *pow2-ness* is typed (`Pow2`
  params); the actual `[rows, cols]` agreement of two operands is **interpret/trace
  checked**, not carried in the type. Carrying full shapes would need `TypeVarTuple`
  dependent shapes that jax 0.10.1's stubs do not express and that mypy cannot ergonomic-
  ally check — and it forecloses no *named* impedance (the four seams are dtype/lib/
  device/pow2, not shape-arithmetic). Per ADR-0000's "a type earns its place by
  foreclosing a class," full shape-typing earns none of the four and is declined.
- **Tile rank (0-d scalar vs 2-d tile) is not phantom-typed.** The band base `Idx0` is an
  `Idx` with a runtime 0-d check at the `band` boundary. Same justification.
- **`einsum` slips mypy** (jax stubs type `*operands: Any`). This is stated, not hidden:
  it is closed at the *construction* surface (§4.lib), not the type surface. Calling it
  "type-closed" would be the unsubstantiated claim ADR-0009 forbids.

These three are the residuals; §4 states the exact surface (interpret-check /
construction-raise / host-gate) that covers each. Nothing is narrated-and-left (ADR-0013
Rule 4): each residual has a named disposition.

---

## 6. How it folds to LOWERABLE jax/Pallas primitives (the constraint, honored)

There is no Triton emission, no `triton.compile`, no `jax.ffi`, no fusion logic. The
"interpreter" is the eager body of each combinator: `unwrap the Tile(s) → call the exact
`jnp`/`pl` expression from the proven kernel → rewrap as `Tile``. Composing combinators
therefore builds an ordinary jaxpr containing only the primitives `pl.dot`, `pl.ds`/
`dynamic_slice`, `iota`, `==`, `*`, `+`, `sum`, `max`, `exp`, `where`, `clip`, `sign`,
`abs`, `log`, `ceil`, `astype` (only inside `to_i32`/`to_f32`) — the band-select +
arithmetic-bucket set already measured lowerable (minus the two host-unknowns). That
jaxpr is handed to `pl.pallas_call(..., compiler_params=plgpu.CompilerParams(...))`, and
**Pallas lowers it and XLA fuses it.** We constrain only the *input* (only lowerable ops
are constructible), so the stack always succeeds on what we hand it; we never out-engineer
it. This is the firm CONSTRAINT, satisfied structurally.

---

## 7. Exactly how it expresses the disentangled-flash kernel

The port is mechanical: each line of `disent_flash_kernel`'s `body` becomes a combinator
call. The math, the bit-identical band-select, the ~1e-5 online-softmax fold, and the
SSOT reuse of `jax_deberta.make_log_bucket_position` are **unchanged** (ADR-0012 P1; the
implement phase ports, it does not re-derive). The mapping:

| `disent_flash_kernel` today | lowerable-algebra expression |
| — | — |
| `q = q_ref[0]` | `q = ops.load(q_ref, block_q, d)` → `Tile[F32]` |
| `arows = qi0 + jnp.arange(block_q)` | `arows = ops.add(ops.iota(block_q), qi0)` → `Idx` |
| `content = pl.dot(q, k.T)` | `content = ops.dot(q, ops.transpose(k))` → `Tile[F32]` |
| `d_ij = arows[:,None] - bcols[None,:]` | `d_ij = ops.sub(row(arows), col(bcols))` → `Idx` |
| `pos = _bucket_index(d_ij, …)` | `pos = ops.bucket_index(d_ij, position_buckets=…, span=…, two_span=…)` → `Idx` |
| `off_min = qi0 - (kj0+block_k-1)` | host `int` arithmetic (stays host — device seam) |
| `b_lo = _bucket_index(off_min,…)` | `b_lo = ops.bucket_index(lift(off_min), …)` → `Idx0` |
| `base = jnp.clip(b_lo, 0, two_span-W)` | `base = ops.clip(b_lo, 0, two_span - int(W))` → `Idx0` |
| `c2p_band = c2p_full_ref[bh, pl.ds(qi0,block_q), pl.ds(base,W)]` | `c2p_band = ops.band(c2p_full_ref, bh, qi0, block_q, base, W)` → `Tile[F32]` |
| `sel = pos - base` | `sel = ops.sub(pos, base)` → `Idx` (provably in `[0,W)`) |
| `onehot = (arange(W)==sel).astype(f32)` | `oh = ops.onehot(sel, W)` → `Tile[F32]` (no gather) |
| `c2p = sum(c2p_band[:,None,:]*onehot, -1)` | `c2p = ops.select(c2p_band, oh, axis=-1)` → `Tile[F32]` (broadcast-`mul`+`rsum`, **NOT einsum**) |
| `s = content + (c2p+p2c)/scale` | `s = ops.add(content, ops.div_scalar(ops.add(c2p, p2c), scale))` |
| `s = where(mask>0, s, neg)` | `s = ops.where(ops.gt(mask, zero), s, neg_tile)` |
| `m_new = maximum(m, max(s,-1))` | `m_new = ops.where(ops.gt(m, ops.rmax(s,-1)), m, ops.rmax(s,-1))` |
| `p = exp(s - m_new[:,None])` | `p = ops.exp(ops.sub(s, col(m_new)))` |
| `l = l*corr + sum(p,-1)` | `l = ops.add(ops.mul(l, corr), ops.rsum(p,-1))` |
| `acc = acc*corr + pl.dot(p, v)` | `acc = ops.add(ops.mul(acc, col(corr)), ops.dot(p, v))` |
| `o_ref[0] = (acc/l).astype(...)` | store boundary (mirror of `load`): `ops.store(o_ref, ops.div(acc, col(l)))` |

(`row`/`col` are `ops.bcast_row`/`ops.bcast_col`, typed broadcasts replacing `[:,None]`/
`[None,:]` so the one-hot/score tiles are built without fancy indexing.) Every dim
(`block_q`, `block_k`, `S`, `d`, `W`) is a `Pow2`. The result is the **same kernel**, now
*unconstructable* in any of the four impedance modes.

`pallas_disentangled_attention` (the `pallas_call` builder) is unchanged except it imports
`Pow2`/`pow2`/`next_pow2` from `nla_lab.lower.shape` (P1 relocation) and its `BlockSpec`
dims are the `Pow2`-branded dims. The fidelity oracle (`exact_reference` via `jax_deberta`)
and `interpret=True` guest validation are unchanged — the algebra changes *how the kernel
is constructed*, not what it computes.

---

## 8. Hygiene / acceptance (owed in full — ADR-0013)

- `mypy --strict` clean, config mirroring `nla_lab/mypy.ini` (jax is real/`py.typed`;
  `jax_deberta` stays the named stub-gap skip). The carrier's non-ArrayLike-ness is the
  load-bearing typed fact — add a mypy regression that asserts `jnp.sum(tile)` and
  `tile[idx]` are type errors and `ops.sum`/`ops.band` are not.
- `pytest`: (a) the demoted `_triton_acl.py` walk as a backstop regression (§4.lib); (b) a
  trace-raise test that `jnp.einsum(tile, …)` raises at `make_jaxpr` (the construction
  backstop); (c) bit-identity of the algebra-built kernel vs the current
  `disent_flash_kernel` under `interpret=True` (the band-select is already proven
  `== 0.0` vs the gather — that contract carries over); (d) `pow2()` rejects `2S−1`.
- jax/jaxlib pinned 0.10.1; interpret/compile only on the guest (no GPU). The sm_75
  lowering of `log`/`ceil`/fp32-`pl.dot` and the carveout grant remain the **host gate**,
  measured on the 2080Ti, filed per ADR-0009 — not claimed here.
- `lower/*.py` added to `test_import_xor.py::SCANNED` and (the math files) to
  `test_device_transfers.py::SCANNED`; the carrier/ops files are device-only (jax, no
  numpy), so they need no `BOUNDARY_FILES` entry.
- Commit as `bork <you@example.com>`; **never push** (background-agent policy).
```
