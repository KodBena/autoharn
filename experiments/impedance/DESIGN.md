# `impedance` — the library-parametric (lib, device, dtype, shape) tensor ACL (settled design)

Status: **SETTLED.** This document is an adjudication, not an options menu. It decides ONE
design and is implemented verbatim next. It is authored to be **extracted to its own public
repository** (the maintainer is tired of re-explaining host↔device costs; this becomes the
reusable SSOT) — so it is standalone, names no chocofarm/fact-mining internals in its public
surface, and its acceptance bar is a clean `mypy --strict` + `pytest` on the package alone.

It **generalizes the library axis** of `nla_lab/lower` (the committed tagless-final four-seam
closure, instantiated for jax/Pallas — read its `DESIGN.md`). `nla_lab/lower` is the
conceptual base and the **jax adapter reference**; this package lifts its single implicit
library (jax) to a **parameter**, so torch, numpy, jax, scipy, … each plug in by writing **one
adapter** and cross-library interface impedances become **unconstructable by construction** (a
`mypy --strict` error, or a non-existent constructor), not lint-detected after the fact.

Authored against **ADR-0000** (illegal states unrepresentable — the four impedances must be
*unconstructable*, not lint-flagged; a type earns its place by foreclosing a *class*), **ADR-0011**
(every discipline declares its enforcement surface; a recurrence converts to a mechanism, and
the package promotion to its own repo is the SSOT this ADR's "load-bearing knowledge in
unenforceable prose" anti-pattern G demands be encoded in *code*), **ADR-0012** P1/P2/P8 (one
home per fact; a boundary translates-and-validates and refuses what it cannot honor; the typed
signature is the contract SSOT), **ADR-0009** (MEASURED — honest about type-closed vs
construction-raise vs runtime), and **ADR-0013** (no de-scope; the full four-seam surface,
parametric, is owed). **The standard:** if you would not trust your mother's life to the effect
of this code, you are not trying hard enough.

> **Evidence (ADR-0009 / ADR-0013 Rule 5 — verify the artifact, not the claim).** Every typed
> closure claim in §2 was checked on a minimal POC under `mypy --strict` before this design was
> settled. The four seam mismatches each produce the predicted diagnostic — device:
> `Argument … has incompatible type "Tensor[Torch, TorchCUDA, F32, Dyn]"; expected
> "Tensor[Torch, TorchCPU, …]" [arg-type]`; lib: `… "Tensor[Torch, …]"; expected
> "Tensor[Jax, …]" [arg-type]`; dtype: `… "Tensor[Jax, JaxCPU, F64, …]"; expected
> "…F32… [arg-type]"`; capability: `"JaxOps" has no attribute "gather" [attr-defined]` — while
> the mediated happy path type-checks clean. The mechanics below are not asserted; they are
> reproduced. The reproduction is promoted to a `pytest` mypy-regression in §6.

---

## 0. The criterion, restated as the bar this design is judged against

Four seam axes — the same four `nla_lab/lower` closed for one library — must be encoded so a
mismatch **at a cross-library crossing** is **unconstructable**, in **one** composable,
library-agnostic SSOT, with a **standardized adapter seam** so adding a library is *just*
writing an adapter:

- **lib** — handing a value owned by library A to an operation of library B (a torch tensor to
  a jax op; a jax array to numpy) without going through a **marked bridge**.
- **device** — host code touching device data or vice versa (a CUDA torch tensor handed to
  numpy without a **marked device transfer**); device residence is *library-relative*
  (torch's `cuda` is not jax's `gpu` is not numpy's host).
- **dtype** — a silent coercion (passing `float64` where `float32` is required; an implicit
  `int→float`); the cast must be explicit and typed.
- **shape** — a shape the target cannot accept (a non-power-of-2 kernel dim; a rank mismatch);
  the constraint is *adapter-declared* (a Pallas adapter demands `Pow2`, a numpy adapter does
  not).

Plus the **capability** closure that `nla_lab/lower`'s "closed surface" already implies and this
package makes first-class: **using a lib op the target adapter does not provide** (a `gather`
on the lowerable-jax adapter) is unconstructable — the capability set *is* the adapter's method
surface, and a missing capability is `[attr-defined]`.

**The firm constraint (inherited verbatim from `nla_lab/lower` §0, generalized):** this is a
**correctness/type layer only.** We do not reimplement any library's math, fusion, kernels, or
scheduling. Each adapter's combinator body is the *exact* native call (`torch.add`,
`jnp.matmul`, `scipy.special.softmax`) it already wraps; we constrain only the *input* to each
library so a cross-seam mismatch cannot be built, then hand the value to the native op
unchanged. We never reach past a library and never out-engineer it.

---

## 1. The nomenclature ruling (the algebra, fixed) and the package layout

`nla_lab/lower` settled the form: a **tagless-final (final-style) typed-combinator embedded
DSL** with a **single opaque, non-coercible carrier** and **smart constructors**, where an
ill-formed kernel is an *ill-typed expression* (no reified term to fold, hence no fold-time
check — the seam closure is a property of the combinator *signatures*, evaluated by mypy at
construction). We **honor that ruling and lift exactly one thing**: the *interpreter*.

In `nla_lab/lower` there is one implicit interpreter (eager jax/Pallas), so the library axis is
invisible. Tagless-final's defining strength is that it **admits multiple interpreters over one
typed surface**. This package makes the interpreter a **parameter**: each library is one
interpreter — an **adapter** — and the carrier gains a **library tag** so the *type system
itself* names which interpreter owns a value. A cross-library expression is then literally an
**ill-typed expression**: an op of interpreter B does not accept a carrier tagged for
interpreter A. This is not a new idea bolted on; it is the second interpreter `nla_lab/lower`
§1.4 explicitly noted was *available and not built* — built, and generalized to N.

Call it, in code and prose, **the library-parametric tensor ACL**: carrier `Tensor[L, Dev, D,
S]`, library-agnostic **core**, per-library **adapters**.

Package layout (one home per concern, ADR-0012 P1/P3; designed for extraction):

```
experiments/impedance/                     # the extraction unit (→ its own github repo)
  DESIGN.md                                # this file (the SSOT)
  pyproject.toml                           # standalone; declares only the core (no lib deps)
  impedance/
    __init__.py                            # public surface: Tensor, the dtype tags, the seam Protocol
    dtype.py                               # SHARED phantom dtype tags: F32/F64/I32/I64/BoolT (core)
    shape.py                               # SHARED shape kinds: Dyn (untracked) + Pow2 (from nla_lab) (core)
    tensor.py                              # the opaque carrier Tensor[L,Dev,D,S] — non-coercible, non-constructable
    adapter.py                             # THE STANDARDIZED ADAPTER SEAM — the Protocol every library implements
    host.py                               # the host interchange carrier (HostBuffer) + the bridge spine (§1.2)
    lib/                                   # one file per adapter — adding a library is adding ONE file here
      __init__.py                          # re-exports the adapter singletons (torch, numpy, jax, scipy)
      numpy_lib.py                         # the HOST adapter (numpy) — also the interchange authority
      torch_lib.py                         # the torch adapter (device model: cpu/cuda)
      jax_lib.py                           # the jax adapter (a thin, general jax interpreter)
      jax_lower_lib.py                     # the jax/Pallas LOWERABLE adapter == nla_lab/lower, as ONE adapter (§3)
      scipy_lib.py                         # the scipy adapter (host-family capabilities over numpy carriers)
  tests/                                   # mypy-regression + runtime parity + brand-raise tests (§6)
  demo/                                    # the toy cross-library pipeline + the before/after (§4)
    pipeline.py                            # the MEDIATED pipeline (reads naturally)
    raw_pipeline.py                        # the RAW library-call mess (the before)
    mismatches.py                          # five deliberate impedances — each a mypy error / brand-raise
```

`pyproject.toml` declares **no** library as a hard dependency: the core (`tensor`/`dtype`/
`shape`/`adapter`/`host`) imports none of {torch, numpy, jax, …}; each adapter imports exactly
its own library, lazily, so `import impedance` is import-light and a consumer pays only for the
adapters it touches. This is the import-XOR posture of the base project, lifted to a clean
package boundary (the core is host-XOR-device-*neutral*; each adapter is single-library).

### 1.2 The bridge spine — why adding a library is O(1), not O(n²)

The naive cross-library design writes a bridge per ordered pair — O(n²), and adding a library
means writing n new bridges, breaking the "*one* adapter" promise. We refuse it. Every crossing
routes through a **single canonical host interchange**: the **host carrier**
`HostBuffer[D, S] := Tensor[Numpy, Host, D, S]`. **numpy is the host adapter** — the natural,
honest choice (the base project already treats numpy as *the* host SSOT). Each adapter provides
exactly **two** host-crossing operations, naming only itself and the host:

- `export_host(x: Tensor[L, HostDev_L, D, S]) -> HostBuffer[D, S]` — pull L's value (already on
  L's host-side device) to the neutral host buffer. The **real** transfer
  (`t.detach().cpu().numpy()`, `np.asarray(jax_arr)`).
- `import_host(b: HostBuffer[D, S]) -> Tensor[L, HostDev_L, D, S]` — push the host buffer into
  L (`torch.from_numpy(b)`, `jnp.asarray(b)`).

A cross-library move A→B is then `B.import_host(A.export_host(x))` — composed from each
adapter's **own** two ops. Adding library X requires only X's `export_host`/`import_host` (+ its
device transfer to reach `HostDev_X`); **no** edit to any other adapter, **no** pairwise matrix.
Both `export_host` and `import_host` **preserve `D` and `S`** in their signatures, so a bridge
**cannot silently change dtype or shape** — the dtype seam survives the crossing for free.

`HostBuffer[D, S]` is itself an opaque `Tensor` (numpy-tagged); the host buffer is a *typed
brand*, not a raw `np.ndarray`, so it cannot leak back into a device adapter except through that
adapter's `import_host`. (Zero-copy via dlpack is an adapter implementation detail behind the
same two-op interface — the *interface* is the contract, the codec is private.)

---

## 2. The four seams in the types — with the honest closure surface

The decisive table. For each seam: the mechanism, and **honestly** whether it is type-closed
(mypy), construction-raise-closed (at the entry/brand boundary), or interpret/runtime. The
carrier is the single SSOT for all five axes (lib/device/dtype/shape + capability), exactly as
`Tile` was for `nla_lab/lower`'s four.

### 2.0 The carrier (`tensor.py`) — the discipline lifted verbatim from `nla_lab/lower`

```python
L   = TypeVar("L")                  # library tag      (Torch / Numpy / Jax / Scipy / JaxLower)
Dev = TypeVar("Dev")                # device tag       (per-library: TorchCPU / Host / JaxCPU …)
D   = TypeVar("D", bound=DType)     # dtype tag        (SHARED core vocabulary: F32 / F64 / I32 …)
S   = TypeVar("S", bound=ShapeKind) # shape kind       (SHARED: Dyn / Pow2 — adapter-declared)

@final
class Tensor(Generic[L, Dev, D, S]):
    """Opaque, NON-ArrayLike, NON-COERCIBLE, NON-CONSTRUCTABLE, NOT a pytree.
    Phantom-typed by (library, device, dtype, shape-kind). Its ONLY surface is the adapter
    combinators. See nla_lab/lower/tile.py — this is that carrier, with three phantom params
    added (L, Dev) and (D, S kept)."""
    __slots__ = ("_raw",)
    def __init__(self) -> None:
        raise TypeError("Tensor is core-private and NON-CONSTRUCTABLE: a Tensor is born ONLY "
                        "inside an impedance adapter combinator. No public ctor, no token.")
```

The four discipline properties of `nla_lab/lower`'s `Tile` are **kept verbatim** (they are
load-bearing and were hardened against three real CRITICALs — see that DESIGN's revision note):

1. **Non-coercible** — no `__array__`, `__jax_array__`, `__array_namespace__`, no arithmetic
   dunders, no `__getitem__`. mypy rejects a `Tensor` wherever an `ArrayLike`/array is expected;
   and at runtime, feeding a `Tensor` to an un-wrapped native op raises (no library can convert
   it). This is the construction-raise backstop for the residual mypy cannot reach (a library's
   `*args: Any` op — `jnp.einsum`, `np.concatenate`).
2. **Non-constructable** — raising `__init__`, **no importable mint token**; the *core* mints a
   `Tensor` only via `object.__new__` inside a package-private `_wrap`, a path a caller cannot
   name (the CRITICAL-1 fix). An adapter calls `_wrap`; a *consumer* never can.
3. **Not a pytree** — an opaque leaf, so no `tree_map` rewrap re-entry vector (the HIGH-2 fix);
   any control-flow carry stays wrap/unwrap-internal to the adapter.
4. **One SSOT, five axes** — `Tensor` is simultaneously the lib brand, the device brand, the
   dtype phantom, and the shape-kind brand; the capability surface is the adapter that accepts
   it. No second mechanism.

### 2.1 lib seam — cross-library handoff → **TYPE-CLOSED (+ construction-raise at entry)**

Every adapter's combinator is **monomorphic in `L`**: `JaxOps.matmul` takes
`Tensor[Jax, Dev, F32, S]`. A `Tensor[Torch, …]` is **not** assignable to `Tensor[Jax, …]`
(`Tensor` is invariant; `Torch` and `Jax` are unrelated marker classes), so handing a torch
value to a jax op is a mypy `[arg-type]` (**verified**). There is **no** combinator anywhere
that takes two different `L`s — a cross-library op is not merely rejected, it is *inexpressible*.
**The only** cross-`L` path is `export_host`/`import_host` through the host carrier (§1.2),
which are explicit, named, diff-visible, and dtype/shape-preserving. **Fully type-closed.**

The **honest residual**: *entering* the ACL — branding a raw `torch.Tensor` the consumer hands
in as `Tensor[Torch, TorchCUDA, F32, Dyn]` — is a **construction-time assertion** at the entry
brand (`torch.brand(raw)`), not a type proof: a raw library tensor's library is known from
*which adapter you called*, but its claimed dtype/device are read off the runtime object and
**verified, raising on mismatch**. This is the exact analog of `nla_lab/lower`'s `ref()` brand
honesty (`§4.device`): the brand is the single, diff-visible host→ACL crossing; once branded,
the lib tag is type-carried and type-checked everywhere downstream. Entry is construction-raise;
*flow* is type-closed.

### 2.2 device seam — host↔device residence → **TYPE-CLOSED in-flow (+ construction-raise at entry)**

Device tags are **per-library** and **bounded**: `class TorchDevice: ...;
class TorchCPU(TorchDevice): ...; class TorchCUDA(TorchDevice): ...`. Three genuinely different
claims, stated separately so none is overclaimed (the `nla_lab/lower` §4.device discipline,
*strengthened* because we own the carrier where jax did not):

- **operand co-residence (type-closed).** Every binary combinator pins `Dev` across its
  operands and result: `add(a: Tensor[L, Dev, D, S], b: Tensor[L, Dev, D, S]) ->
  Tensor[L, Dev, D, S]`. A `cpu + cuda` add is a mypy `[arg-type]` — the two `Dev`s do not
  unify. This is **stronger than** `nla_lab/lower`, which could only operand-check relabeled
  device because stock `jax.Array` carries no residence tag; here residence is a genuine phantom
  the carrier owns.
- **cross-library residence (type-closed).** `export_host` accepts only `Tensor[L, HostDev_L,
  D, S]` — L's *host-side* device. A `Tensor[Torch, TorchCUDA, …]` does **not** satisfy
  `export_host`'s `TorchCPU` requirement (**verified**), so "a CUDA torch tensor to numpy
  without a marked transfer" is **unconstructable**: you must first call `torch.to_device(x,
  TorchCPU)` — the explicit, named device transfer (the real `.cpu()`) — *then* `export_host`.
  The device move is forced into the open, in the types.
- **entry residence (construction-raise).** Branding a raw tensor's device
  (`torch.brand(raw, dev=TorchCUDA)`) **reads `raw.device` and verifies it**, raising on
  mismatch — a boundary *assertion*, not a proof, because a raw library object's residence is a
  runtime fact. Honest, single-home, diff-visible; identical posture to `nla_lab/lower`'s `ref`.

`to_device` is the per-library marked transfer: `to_device(x: Tensor[Torch, Any, D, S],
dev: type[TD]) -> Tensor[Torch, TD, D, S]` with `TD` bound to `TorchDevice` — so a `JaxCPU`
target on `torch.to_device` is a mypy `[type-var]` (you cannot move a torch tensor to a jax
device; that is a *bridge*, not a transfer). The device **set** of a library is exactly the
subclasses of its `*Device` base — the adapter *describes its device model* by declaring that
family and which member is `HostDev_L`.

### 2.3 dtype seam — silent coercion → **TYPE-CLOSED (the cast); runtime (the lowering)**

`D` is a **shared** phantom over the core vocabulary (`F32`/`F64`/`I32`/`I64`/`BoolT`). The same
tag instance flows across every library and every bridge, so `Tensor[Torch, TorchCPU, F32, S]`
and `Tensor[Numpy, Host, F32, S]` share *one* `F32` — which is exactly what lets a bridge
preserve dtype in its signature (§1.2) and an op pin it across operands. Two closures:

- **the coercion is type-closed.** Every combinator pins `D`: `matmul` requires both operands
  `F32` and returns `F32`; `add` keeps `D`. Passing `F64` where `F32` is required is a mypy
  `[arg-type]` (**verified**). The **only** `D`-changing operation is the explicit per-adapter
  `cast(x: Tensor[L, Dev, Any, D_in...], dt: type[D2]) -> Tensor[L, Dev, D2, S]` — a named,
  diff-visible, single-home event (`nla_lab/lower`'s `to_i32`/`to_f32`, generalized to any
  dtype pair an adapter supports). `Tensor` exposes no `.astype`. A silent coercion is
  **unconstructable** — to change dtype you must *write `cast(...)`*.
- **the dtype set is adapter-declared; an unsupported dtype is construction-raise.** Adapters
  support different dtype subsets (numpy has them all; a hypothetical int8-only kernel adapter
  does not). The adapter *describes its dtype model* by which `type[D]` its constructors/`cast`
  accept; an unsupported tag passed dynamically raises at construction (the adapter's
  `_concrete(tag)` dispatch — `nla_lab/lower/ops._jnp_dtype`'s pattern). The orthogonal "does
  this library's op *run* on this device for this dtype" (e.g. an sm_75 lowering of `log`) is
  **runtime**, never claimed in the types — `nla_lab/lower` §4.dtype's honesty, inherited.

### 2.4 shape seam — a shape the target cannot accept → **adapter-declared; TYPE-CLOSED (Pow2/rank) + construction-raise (runtime dims)**

`S` is a **shared, adapter-declared shape kind** bounded by `ShapeKind`. The core ships two,
and an adapter *describes its shape model* by which it brands its tensors with:

- **`Dyn`** — the untracked dynamic shape. Operand-shape *agreement* (`[m,k]·[k,n]`) is
  **interpret/runtime-checked**, not type-carried — the deliberate, honest stop of
  `nla_lab/lower` §5 (full shape tuples are not phantom-typed: jax/torch stubs do not express
  `TypeVarTuple` dependent shapes ergonomically, and full shape-typing forecloses none of the
  *named* impedances). The demo's general-purpose adapters use `Dyn`, so the pipeline reads
  naturally and shape-agreement is a clear runtime error, not type noise.
- **`Pow2`** — the power-of-2 brand, **lifted verbatim from `nla_lab/lower/shape.py`**
  (`pow2()` is its only source and validates). A kernel/Pallas adapter (`jax_lower_lib.py`, §3)
  *describes its shape model as `Pow2`*: its constructors take `Pow2` dims, so a raw `int`
  dimension is a mypy `[arg-type]` and the `2S−1` trap cannot be branded `Pow2`
  (construction-raise on a runtime-derived non-pow2). The shape seam is thus **type-closed where
  the constraint is a static brand** (Pow2, or a rank kind) and **construction-raise for a
  runtime dim** — `nla_lab/lower` §4.shape, now *parametric*: each adapter declares its own
  shape constraint, and a `Pow2`-demanding adapter cannot be handed a `Dyn` tensor (the
  shape-kinds do not unify).

### 2.5 capability seam — an op the target does not support → **TYPE-CLOSED (`[attr-defined]`)**

The **lib-capability set IS the adapter's method surface.** Where `nla_lab/lower` made "closed
surface" a property of one `ops.py` (no `gather`/`einsum`/`astype`), this package makes it
first-class and *per-adapter*: the lowerable-jax adapter has no `gather` method, so
`jax_lower.gather(x)` is a mypy `[attr-defined]` (**verified**) — the op does not exist on that
interpreter. A *different* jax adapter (`jax_lib.py`, the general one) **may** expose `gather`;
the capability seam is precisely that capabilities differ by adapter and a missing one is a
type error, not a runtime surprise. This is the cleanest of the five closures and it is the one
the standardized-adapter framing buys us for free: the adapter *describes its capability set* by
*being* a class whose methods are exactly its capabilities.

### The closure theorem (the spine, stated once, generalized from `nla_lab/lower` §4)

> A pipeline authored in this ACL is a composition of adapter combinators over `Tensor`s.
> Because the carrier is non-coercible and non-constructable, the **only** way to produce a
> `Tensor` from `Tensor`s is an adapter combinator; **every** combinator is monomorphic in `L`,
> pins `Dev` and `D` across its operands, and brands `S` with its adapter's shape kind; and the
> **only** cross-library path is the explicit `export_host`/`import_host` bridge, which
> preserves `D` and `S`. Therefore a pipeline that (i) type-checks under `mypy --strict` is — by
> construction — free of un-bridged cross-library handoffs (lib), free of un-transferred
> cross-device handoffs (device), free of silent dtype coercion at every crossing (dtype), and
> free of capability misuse (an op the target lacks); and any shape constraint an adapter
> *declares statically* (Pow2 / rank) is met. The illegal crossing is unconstructable: either
> mypy rejects it (wrong lib/device/dtype/capability/shape-kind), or — for the residuals named
> honestly above — a brand raises at entry or `pow2()` raises on a runtime dim.

The classes the theorem **cannot** cover, named loudly (ADR-0013 Rule 4 — named, not
narrated-and-left): (a) the **entry brand** asserts a raw object's claimed device/dtype at
construction, it does not prove them (a raw object carries no residence/dtype tag a type can
read); (b) **full shape agreement** on `Dyn` adapters is interpret-checked, not type-carried;
(c) whether a *capability-legal* op actually *runs* on a given backend/device/dtype is runtime
(the `nla_lab/lower` sm_75 host-gate, generalized). Each has a named disposition in §6.

---

## 3. The standardized adapter interface (so adding a library is JUST writing an adapter)

This is the centerpiece. The adapter surface splits into **two layers**, and the split *is* the
answer to "the location/shape of the adapter interface is standardized while every library is
different":

- **The SEAM protocol — STANDARDIZED, identical for every library.** This is the fixed-shape
  interface a library implements; it carries the *device model*, *dtype model*, *shape model*,
  and the *seam-crossing operations*. It is a `typing.Protocol` (a structural typeclass) so an
  adapter satisfies it by shape, not by inheritance. Writing this is **all** that "adding a
  library" requires.
- **The CAPABILITY surface — PER-LIBRARY, genuinely different.** The math combinators
  (`add`/`matmul`/`relu`/`softmax`/`gather`/…). This is *not* standardized and *must not* be:
  the capability seam (§2.5) is exactly that capability sets differ, and a missing capability is
  `[attr-defined]`. The adapter declares its capability set by *being a class whose methods are
  its capabilities*.

### 3.1 The seam protocol (`adapter.py`) — the exact typeclass a library implements

```python
Lib  = TypeVar("Lib")                       # this adapter's library tag
HDev = TypeVar("HDev")                       # this adapter's HOST-side device tag
Dev2 = TypeVar("Dev2"); D2 = TypeVar("D2", bound=DType); Sx = TypeVar("Sx", bound=ShapeKind)

class LibAdapter(Protocol[Lib, HDev]):
    """The STANDARDIZED seam every library plugs into. Implement this and you have an adapter;
    the four seam descriptors + five crossing ops are the whole obligation. The capability
    combinators live on the concrete adapter class, NOT here (they differ per library — §2.5)."""

    # ---- (i) DEVICE MODEL ------------------------------------------------------------------
    # The library's device family is the bound of its *Device base; HOST_DEVICE names the one
    # member export_host/import_host cross. `to_device` is the marked in-library transfer.
    HOST_DEVICE: type[HDev]
    def to_device(self, x: Tensor[Lib, Any, D, S], dev: type[Dev2]) -> Tensor[Lib, Dev2, D, S]: ...

    # ---- (ii) DTYPE MODEL ------------------------------------------------------------------
    # `supports_dtype` is the declared dtype set; `cast` is the ONLY in-library D-change.
    def supports_dtype(self, dt: type[DType]) -> bool: ...
    def cast(self, x: Tensor[Lib, Dev, Any, S], dt: type[D2]) -> Tensor[Lib, Dev, D2, S]: ...

    # ---- (iii) SHAPE MODEL -----------------------------------------------------------------
    # The adapter's shape kind (Dyn or Pow2 …): `reshape` rebrands; constructors take it.
    def shape_kind(self) -> type[ShapeKind]: ...

    # ---- (iv) ENTRY/EXIT BRANDS + THE BRIDGE SPINE (the seam-crossing ops, §1.2) ------------
    def brand(self, raw: object, *, dev: type[Dev2], dt: type[D2]) -> Tensor[Lib, Dev2, D2, Dyn]: ...
    def unwrap(self, x: Tensor[Lib, Any, Any, Any]) -> object: ...        # ACL → raw, at the exit boundary
    def export_host(self, x: Tensor[Lib, HDev, D, S]) -> Tensor[Numpy, Host, D, S]: ...
    def import_host(self, b: Tensor[Numpy, Host, D, S]) -> Tensor[Lib, HDev, D, S]: ...
```

That `Protocol` is the **entire** standardized contract. Note what it pins and what it leaves
open:

- It pins the **shape of every crossing** (`to_device`, `cast`, `brand`, `export_host`,
  `import_host`) so cross-library/-device/-dtype moves have *one* identical shape regardless of
  library — the maintainer learns the seam once and it is the same for torch as for jax.
- It pins **lib-monomorphism**: every method's input and output carry `Lib`, so an adapter
  *cannot even be written* to accept another library's tensor in a seam op.
- It pins **dtype/shape preservation** across `export_host`/`import_host` (same `D`, same `S`),
  closing the dtype seam across the bridge by construction.
- It **does not** enumerate capabilities — those are the concrete adapter's own methods.

Adding a library = writing one class with these ~7 members. The host bridge spine in `host.py`
needs **zero** edits (it composes any two adapters' `export_host`/`import_host`). This is the
O(1)-per-library promise, mechanized by the protocol shape.

### 3.2 A concrete adapter (torch) — the capability surface beside the seam

```python
class TorchDevice: ...
class TorchCPU(TorchDevice): ...
class TorchCUDA(TorchDevice): ...

class TorchAdapter:                         # satisfies LibAdapter[Torch, TorchCPU] structurally
    HOST_DEVICE = TorchCPU
    # --- seam ops (the standardized part) ---
    def to_device(self, x, dev): ...        # body: t.to(_torch_device(dev))   [the real transfer]
    def cast(self, x, dt): ...              # body: t.to(_torch_dtype(dt))      [the real cast]
    def export_host(self, x): ...           # body: _wrap_np(t.detach().cpu().numpy())
    def import_host(self, b): ...           # body: _wrap_t(torch.from_numpy(_np(b)))
    def brand(self, raw, *, dev, dt): ...   # reads raw.device/raw.dtype, VERIFIES, raises on mismatch
    # --- capability surface (per-library; the lib seam by presence/absence) ---
    def matmul(self, a: Tensor[Torch, Dev, F32, S], b: Tensor[Torch, Dev, F32, S]) -> Tensor[Torch, Dev, F32, S]: ...
    def relu(self,   a: Tensor[Torch, Dev, F32, S]) -> Tensor[Torch, Dev, F32, S]: ...
    def add(self,    a: Tensor[Torch, Dev, D, S],   b: Tensor[Torch, Dev, D, S])   -> Tensor[Torch, Dev, D, S]: ...

torch: Final = TorchAdapter()               # the singleton the demo imports as `torch`
```

Every capability body is **one native call** wrapped `unwrap → torch.* → _wrap` — we add no
math, exactly `nla_lab/lower/ops.py`'s eager-interpreter discipline. The adapter singleton holds
no mutable state; it is a pure interpreter object.

### 3.3 How `nla_lab/lower` lifts to parametric — jax becomes ONE adapter

`nla_lab/lower` *is* this package's `jax_lower_lib.py`, with the implicit library made explicit.
The mapping is mechanical (ADR-0012 P1 — the port relocates, it does not re-derive):

| `nla_lab/lower` (one implicit interpreter) | `impedance` (`jax_lower_lib.py`, L = `JaxLower`) |
| — | — |
| `Tile[D]` (carrier) | `Tensor[JaxLower, JaxDev, D, Pow2]` — same carrier, 3 phantom params added |
| `Tile` non-coercible / non-constructable / not-a-pytree | **kept verbatim** on `Tensor` (§2.0) |
| `ops.py` free functions (`add`, `dot`, `band`, `onehot`, `select`, …) | the **capability surface** of `JaxLowerAdapter` (methods) |
| the *closed* surface (no `gather`/`einsum`/`astype`) | the adapter's capability set — `gather` absent ⇒ `[attr-defined]` (§2.5) |
| `Pow2` shape SSOT (`shape.py`) | the core `shape.Pow2`; this adapter *declares* `shape_kind() == Pow2` |
| `to_i32` / `to_f32` (the only dtype crossings) | this adapter's `cast` (the standardized dtype op) |
| `Ref` brand + `ops.ref()` (host-array→device-ref) | this adapter's `brand` (the standardized entry op) + `import_host` |
| `fold_kt` (the bounded control-flow carry) | a `JaxLower`-specific capability method (control flow is a capability) |
| the four-seam closure theorem (§4) | the §2.5 closure theorem, the `JaxLower` row of it |

Two things this lift *clarifies*, that were implicit in `nla_lab/lower`:

1. **"Lowerable-only" is a property of an ADAPTER, not of jax.** `nla_lab/lower` constrained
   *jax* to lowerable ops by hand-curating one `ops.py`. Parametrically, that is just *one* jax
   adapter (`jax_lower_lib`) whose capability set excludes `gather`/`einsum`; a *second* jax
   adapter (`jax_lib`) can expose them for non-kernel work. The capability seam (§2.5) is what
   keeps a `JaxLower` tensor from wandering into a `gather` — and a different jax interpreter is
   now a first-class, type-distinct thing, not a fork of one file.
2. **The device seam gets genuinely stronger.** `nla_lab/lower` §4.device admitted it could only
   *brand* (`Ref`) because stock `jax.Array` carries no residence tag. In the parametric carrier
   we own `Dev` as a real phantom, so in-flow residence is type-closed (§2.2); the brand-as-
   assertion honesty is confined to the *entry* boundary, where it genuinely belongs.

The committed `nla_lab/lower` is **not edited** (it remains the jax adapter reference and avoids
racing other work); `jax_lower_lib.py` is its parametric *port*, and a `pytest` asserts the port
is value-identical to it on the disentangled-flash fixture under `interpret=True` (§6).

---

## 4. The toy cross-library demo (the proof of type-sanity + ergonomics)

A small, **readable** pipeline that crosses **four** of {torch, numpy, jax, scipy} (≥3 owed),
all present in the generic venv (`torch 2.12.1+cpu`, `numpy 2.4.6`, `scipy 1.17.1`,
`jax 0.10.1`) — **no install, jax/jaxlib pin untouched.** (sklearn is offered as an optional 5th
adapter — `sklearn_lib.py`, a host-family adapter over numpy carriers — installed only if
present; the demo does not depend on it, so the jax pin is never at risk.) The pipeline is a
distilled, honest descendant of where this project *started* — the spaCy/torch/numpy/jax tangle
of `extract.py` and friends — reduced to a clean "embed → host-normalize → score" loop:

**The mediated pipeline (`demo/pipeline.py`) — reads as a straight line:**

```python
from impedance.lib import torch, numpy as host, jax        # the adapters (not the real libs)
from impedance.dtype import F32
from impedance.shape import Dyn

def score(w, h, qT):                                       # all branded F32 on entry
    e   = torch.relu(torch.matmul(w, h))                   # Tensor[Torch, TorchCPU, F32, Dyn]
    eh  = torch.export_host(e)                             # Tensor[Numpy, Host, F32, Dyn]  (real .cpu().numpy())
    nh  = host.softmax(eh, axis=-1)                        # scipy.special.softmax, stays host
    yj  = jax.import_host(nh)                               # Tensor[Jax, JaxCPU, F32, Dyn]  (real jnp.asarray)
    return jax.sum(jax.matmul(yj, qT), axis=-1)            # Tensor[Jax, JaxCPU, F32, Dyn]
```

torch → numpy(+scipy) → jax: three marked crossings, each a one-token, dtype/shape-preserving
bridge; every device transfer and dtype cast that happens is *named on the line where it
happens*. The maintainer reads ergonomics off this: the seam is invisible-when-correct and
the types are **inferred** (the verbosity lives in the adapter definitions, written once, not in
the pipeline, read often).

**The raw pipeline (`demo/raw_pipeline.py`) — the before:** the same math as a pile of native
calls — `e.detach().cpu().numpy()`, a silent `.astype(np.float32)` papering a dtype drift, a
bare `jnp.asarray`, a manual `if x.is_cuda` device juggle, and **no** guard against handing a
CUDA tensor to numpy or `float64` to the jax matmul. The before/after is short and the contrast
is the point: the raw version *can* be written wrong four ways and looks fine; the mediated
version *cannot* be written wrong and looks cleaner.

**The impedance snippets (`demo/mismatches.py`) — five deliberate crossings that DO NOT BUILD.**
Each is a few lines, annotated with the exact diagnostic, and a `pytest` runs `mypy --strict` on
this file and asserts the precise error codes fire (the mechanism is **verified**, §0):

| # | crossing | the illegal line | closure |
| — | — | — | — |
| a | **device** | `torch.export_host(cuda_tensor)` — CUDA, not CPU | `[arg-type]` (CUDA ≠ `HostDev_Torch`) |
| b | **lib** | `jax.matmul(torch_tensor, y)` — skipped the bridge | `[arg-type]` (Torch ≠ Jax) |
| c | **dtype** | `jax.matmul(f64_a, f64_b)` — F64 where F32 required | `[arg-type]` (F64 ≠ F32) |
| d | **shape** | `jax_lower.zeros(127, …)` — a non-pow2 kernel dim | `[arg-type]` (`int` ≠ `Pow2`) / `pow2()` raises a runtime dim |
| e | **capability** | `jax_lower.gather(y)` — op the lowerable adapter lacks | `[attr-defined]` |

`(a)`–`(c)`,`(e)` are **mypy-closed** (verified in §0); `(d)` is mypy-closed for a static
literal dim and construction-raise for a config-derived one — the honest split of §2.4. A sixth,
runtime snippet shows the **entry brand raising** when a raw tensor's actual device contradicts
the claimed brand (§2.1 residual) — demonstrating the one construction-raise honestly, not
hiding it behind the types.

---

## 5. Ergonomics as a first-class constraint (how the surface stays natural)

The bar is type-sane **and** ergonomic; the maintainer judges ergonomics by *reading the demo*.
The design choices that buy readability without weakening closure:

1. **Inference carries the verbosity.** The user writes ops and binds results to names; the four
   phantom params are *inferred*, never spelled in the pipeline. The full `Tensor[L, Dev, D, S]`
   appears only in adapter definitions (authored once) and the mismatch table (where being
   explicit is the point).
2. **Adapters are singletons read as library handles.** `torch.matmul(...)`,
   `host.softmax(...)`, `jax.import_host(...)` read like the libraries they mediate — the seam
   is *familiar*, not a new vocabulary. The crossing ops have the *same* names on every adapter
   (`export_host`/`import_host`/`to_device`/`cast`/`brand`) — learn the seam once.
3. **The happy path has no ceremony.** A correct crossing is one token (`torch.export_host(e)`);
   there is no per-call config, no context manager, no explicit type argument on the hot line.
4. **The errors are early and legible.** A mismatch is a `mypy --strict` `[arg-type]` /
   `[attr-defined]` naming both the offending and expected `Tensor[…]` — the diagnostic *is* the
   four-axis story (the verified messages in §0 read as English: "Torch where Jax expected").
5. **Per-library aliases shorten the rare explicit annotation.** `impedance.lib.torch` ships
   `F32CPU[S] = Tensor[Torch, TorchCPU, F32, S]` etc., so the few places a signature is written
   stay short.

ADR-0000's anti-over-typing caveat is honored: we type the *four named* impedances and stop
(full shape arithmetic and rank-on-`Dyn` are declined, §2.4) — a type earns its place by
foreclosing a *class*, and these four classes are the ones that reached the host.

---

## 6. Hygiene / acceptance (owed in full — ADR-0013; the extraction bar)

- **`mypy --strict` clean** on the whole package, and the **mypy-regression** is load-bearing:
  `tests/test_mismatches_dont_typecheck.py` runs `mypy --strict` on `demo/mismatches.py` and
  asserts each of the five crossings emits its predicted error code (the §0 reproduction,
  promoted to a gate — ADR-0011 Rule 1: the closure claim is a *test*, not prose). A companion
  asserts `demo/pipeline.py` type-checks **clean**.
- **`pytest` runtime parity** (ADR-0009 P6 two-tier bar): the mediated pipeline computes
  **bit-identically** to the raw pipeline on a fixed fixture (all discrete + float32 reorder-free
  here, so `==`; where a bridge's dtype is genuinely float-reordered it drops to the aggregate
  bar, stated). Real transfers are exercised: `torch → numpy` (`.cpu().numpy()`) and
  `numpy → jax` (`jnp.asarray`) actually move data, not relabel it.
- **`jax_lower_lib` value-identity:** a `pytest` asserts the parametric jax/Pallas port is
  value-identical to the committed `nla_lab/lower` on the disentangled-flash fixture under
  `interpret=True` — the lift of §3.3 changed *how* the kernel is constructed, not *what* it
  computes.
- **Brand-raise tests:** the entry brand raises when a raw tensor's actual device/dtype
  contradicts the claimed brand (the §2.1/§2.2 construction-raise residual, proven to fire).
- **Carrier-discipline regressions** (lifted from `nla_lab/lower` §8): assert `np.asarray(t)` /
  `t[idx]` / `jnp.sum(t)` are type errors (non-coercible), and that `Tensor(...)` raises and is
  a mypy `[call-arg]` (non-constructable, no token).
- **jax/jaxlib pinned 0.10.1**, verified after any optional install; the core declares no
  library dep; each adapter imports only its own library, lazily. **Standalone**: the package
  runs and tests green with **zero** reference to fact-mining/chocofarm internals (the extraction
  bar — it is its own repo on day one).
- **No-install default:** the demo uses only present libraries (torch/numpy/scipy/jax). sklearn
  is an optional adapter, skipped if absent; the jax pin is never touched by the demo.
- Commit as `bork <you@example.com>`; **never push** (background-agent policy).

---

## 7. What this design does NOT do (honest boundaries — ADR-0009 / ADR-0000)

- It does **not** type full shapes (`[m,k]·[k,n]`) on `Dyn` adapters — operand agreement is
  interpret-checked (§2.4). A `Pow2`/rank kind is typed; full extents are not (the named stop).
- It does **not** prove a *raw* object's residence/dtype at entry — the brand asserts and
  raises (§2.1/§2.2). Once branded, flow is type-closed.
- It does **not** guarantee a capability-legal op *runs* on a given backend/device/dtype — that
  is runtime (the `nla_lab/lower` sm_75 host-gate, generalized).
- It does **not** reimplement any library's math, fusion, or kernels — every combinator body is
  the native call (§0). This is a correctness/type layer, nothing more.

Each of the three residuals has a named disposition (a brand-raise test, an interpret-check, a
runtime gate) — none is narrated-and-left (ADR-0013 Rule 4).

---

## 8. Revision — 2026-06-30: device-model closure + the `JaxLower` bridge entry (post-critique)

*(Dated append per ADR-0005 Rule 8 / ADR-0000 Rule 2 — an adversarial critique identified two
representable-illegal-state classes the first implementation left open; the foreclosing TYPES were
applied in full rather than disclosed as residue. The §3.1 Protocol sketch and §2.2 device prose
above describe the pre-revision shape; this section records the implemented closure.)*

**(D1) The device MODEL is closed, not just device co-residence.** §3.1's `LibAdapter` took its
`to_device`/`brand` target as an unbounded `type[_Dev2]`, so a torch tensor could be *typed* onto a
JAX device (`torch.to_device(x, JaxGPU)` built clean) — the residence tag was forgeable, exactly the
representable-illegal-state ADR-0000 forbids. **Fix:** the seam Protocol gains a third parameter,
`LibAdapter(Protocol[Lib, HDev, DevBase])`, and `to_device`/`brand` accept `type[DevBase]`; each
concrete adapter narrows the family to its own base via a bounded method var (`_TDev = TypeVar(bound=
TorchDevice)`, etc.), which still **structurally conforms** to the standardized Protocol (verified).
A foreign device tag is now a mypy `[type-var]` at both the in-flow transfer and the entry brand —
the device crossing is *unconstructable*, regressioned as `demo/mismatches.py` (f)/(g). The §2.2
honest-residual paragraph ("`to_device` keeps its target unbounded") is **superseded**: only the
*runtime fact* of a raw object's residence is construction-raise; the residence *tag* is type-closed.

**(D2) The `JaxLower` centerpiece composes through the bridge (`as_pow2`).** The lowerable adapter's
capabilities are `Pow2`-only, but `import_host`/`brand` necessarily yield `Dyn` (a host buffer
carries no static pow2 proof), so external data could not *enter* it — the adapter was bridge-
isolated and absent from the demo. **Fix:** a checked `as_pow2(x: …Dyn) -> …Pow2` shape-kind entry —
the honest construction-raise **dual of `pow2()`** (it reads the runtime shape and brands `Pow2`
only if every dim is a power of two, else raises). External host data now enters via
`jax_lower.as_pow2(bridge(host, jax_lower, nh))`, and **the demo routes a real
torch→host→scipy→jax_lower→jax line through it** (five libraries), proving uniform composition.
Tested: promotion admits a `[4,4]` buffer and a `Pow2`-only op runs on it; a `[3,4]` buffer raises.

**(D3/D5/D6/D7) honest scope-limits, stated plainly in README §"What it does not give"** rather than
left for the maintainer to rediscover: shape closure is KIND (Dyn/Pow2/non-pow2-dim), not full
rank/extent (§2.4, the named stop); the dtype/shape-kind vocabularies are core enums, so a genuinely
new *element type* or *shape model* is a one-line core edit (parametric cleanly over lib/device/
capability); the host spine forbids a direct device→device bridge by signature (a deliberate O(1)
choice; dlpack zero-copy lives behind the two-op interface); and `_wrap`/`numpy.to_device` are
ADR-0009-disclosed reflection/relabel residue scoping the guarantee to "no *accidental* impedance."
