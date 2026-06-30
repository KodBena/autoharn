# `impedance` — the library-parametric (lib, device, dtype, shape) tensor ACL

Cross-library tensor plumbing is where the bugs live: a CUDA tensor handed to numpy without a
transfer, a `float64` silently flowing where `float32` was required, a torch value passed to a jax
op, a non-power-of-2 dim handed to a kernel. `impedance` makes **each of these unconstructable** —
a `mypy --strict` error or an unconstructable value, not a runtime surprise or a lint you can
ignore — behind **one standardized adapter seam** so that *adding a library is writing one file*.

It is a **correctness / type layer only**. It reimplements no library's math: every combinator body
is the exact native call (`torch.matmul`, `jnp.exp`, `scipy.special.softmax`) it already wraps. It
constrains only the *input* to each crossing so a mismatch cannot be built, then hands the value to
the native op unchanged.

The design rationale, the four-seam closure theorem, and the ADR provenance are in
[`DESIGN.md`](DESIGN.md) (the SSOT). This README is the operator's view: what it gives, how to add a
library, and how the toy demo proves it.

## The carrier and the five axes

One opaque carrier, phantom-typed by four axes, with capability as the fifth (the adapter's method
surface):

```python
Tensor[L, Dev, D, S]   #  L = library tag   Dev = device tag   D = dtype tag   S = shape-kind tag
```

`Tensor` is **non-coercible** (no `__array__`/`__getitem__`/arithmetic dunders — a raw `np.sum(t)` or
`t[i]` does not type-check, and feeding it to an un-wrapped native op raises at runtime),
**non-constructable** (the public ctor raises; there is no importable mint token), and **not a
pytree** (no `tree_map` rewrap re-entry). Its only surface is the adapter combinators. The discipline
is lifted verbatim from `nla_lab/lower`'s `Tile`, with the `(L, Dev)` phantom params added.

## The per-axis closure table (honest — type-closed vs construction-raise vs runtime)

| Axis | The impedance foreclosed | How | Closure |
| — | — | — | — |
| **lib** | library A's value into library B's op (torch → jax) without the marked bridge | every combinator is monomorphic in `L`; the only cross-`L` path is `export_host`/`import_host` | **type-closed** `[arg-type]` (in-flow); entry brand is construction-raise |
| **device — host crossing** | a CUDA tensor to numpy without a marked transfer | `export_host` requires the host-side device `HDev`; a non-host tensor cannot reach it | **type-closed** `[arg-type]` |
| **device — model** | a torch tensor *typed as resident* on a jax device (the forge) | `to_device`/`brand` bound their target to the library's own `DevBase` family | **type-closed** `[type-var]` |
| **device — co-residence** | a `cpu @ cuda` op within one library | every binary op pins `Dev` across operands (invariant) | **type-closed** (reports as `[misc] Cannot infer` — see below) |
| **device — entry** | a raw object's *actual* residence | `brand` reads `raw.device` and verifies, raising on mismatch | **construction-raise** (a runtime fact no type can read) |
| **dtype — coercion** | `float64` where `float32` is required; an implicit cast | every combinator pins `D`; the only `D`-change is the explicit `cast(x, F32)` | **type-closed** `[arg-type]` |
| **dtype — support** | a dtype an adapter does not realize | `supports_dtype` / the adapter's `_concrete` dispatch | **construction-raise** |
| **shape — kind** | a `Dyn` value into a `Pow2`-only kernel adapter | the kinds do not unify | **type-closed** `[arg-type]` |
| **shape — static dim** | a non-pow2 kernel dimension (the `2S−1` trap) | `Pow2Dim` is minted only by `pow2()`, which validates; `as_pow2` promotes a `Dyn` tensor with a runtime check | a raw `int` is **type-closed** `[arg-type]`; a runtime dim is **construction-raise** |
| **shape — extent** | a `[3,4]·[3,4]` rank/extent mismatch on `Dyn` adapters | — | **runtime** (the named honest stop — see below) |
| **capability** | an op the target adapter does not provide (`gather` on the lowerable adapter) | the capability set *is* the adapter's method surface | **type-closed** `[attr-defined]` |

Every row of this table is a **test, not a claim**: `tests/test_typecheck.py` runs `mypy --strict`
on `demo/mismatches.py` and asserts each crossing emits exactly its code; the clean mediated demo
type-checks clean; `tests/test_brand_raises.py` proves the construction-raises fire.

## Adding a library = writing one adapter

The whole obligation of "add a library" is **one class** implementing the standardized seam
Protocol `LibAdapter[Lib, HDev, DevBase]` (`impedance/adapter.py`): the **device model**
(`HOST_DEVICE` + `to_device`), the **dtype model** (`supports_dtype` + `cast`), the **shape model**
(`shape_kind`), and the **entry/exit + bridge ops** (`brand` / `unwrap` / `export_host` /
`import_host`). The host bridge spine needs **zero** edits — it composes any two adapters'
`export_host`/`import_host` through the single numpy host interchange, so cross-library is O(1) per
library, no n² bridge matrix. The **capability surface** (the math combinators) is deliberately
*not* in the Protocol — it differs per library, and that difference *is* the capability seam.

A worked sketch — **cupy in ~25 lines, zero core edits** (illustrative; cupy is not a dependency):

```python
import cupy as cp, numpy as np
from impedance.adapter import LibAdapter
from impedance.dtype import DType, F32, F64, I32, I64
from impedance.host import Host, Numpy
from impedance.shape import Dyn, ShapeKind
from impedance.tensor import Tensor, _unwrap, _wrap

class CupyDevice: ...                 # the device-family base (the DevBase bound)
class CupyGPU(CupyDevice): ...        # cupy's residence (its host-side device, for this sketch)
class Cupy: ...                       # the library tag
_CDev = TypeVar("_CDev", bound=CupyDevice)   # bounds to_device/brand to cupy's own family
_CP = {F32: cp.float32, F64: cp.float64, I32: cp.int32, I64: cp.int64}

class CupyAdapter:                    # satisfies LibAdapter[Cupy, CupyGPU, CupyDevice]
    HOST_DEVICE: type[CupyGPU] = CupyGPU
    def to_device(self, x, dev: type[_CDev]): return _wrap(cp.asarray(_c(x)))
    def supports_dtype(self, dt): return dt in _CP
    def cast(self, x, dt): return _wrap(_c(x).astype(_CP[dt]))
    def shape_kind(self): return Dyn
    def brand(self, raw, *, dev: type[_CDev], dt): ...   # read .dtype, verify, _wrap
    def unwrap(self, x): return _c(x)
    def export_host(self, x): return _wrap(cp.asnumpy(_c(x)))      # the REAL device->host copy
    def import_host(self, b): return _wrap(cp.asarray(_unwrap(b)))  # the REAL host->device copy
    # --- capability surface (per-library; not standardized) ---
    def matmul(self, a, b): return _wrap(_c(a) @ _c(b))

cupy = CupyAdapter()
_seam_check: LibAdapter[Cupy, CupyGPU, CupyDevice] = cupy   # mypy enforces conformance
```

That is the entire integration. `bridge(torch, cupy, x)` and `bridge(cupy, jax, y)` now work with no
edit to torch, jax, numpy, the host spine, or the core — the O(1)-per-library promise. A library that
shares numpy's memory model and owns no array type (scipy, scikit-learn) plugs in even more cheaply,
as a **capability surface over the numpy host carrier** — see `impedance/lib/scipy_lib.py` and the
optional `sklearn_lib.py` (one file each, no `LibAdapter` at all).

**The one caveat (be honest):** this is fully parametric over **lib, device, and capability**. The
dtype vocabulary `{F32,F64,I32,I64,BoolT}` and shape kinds `{Dyn,Pow2}` are **core enums**, so a
library needing a genuinely new *element type* (`bfloat16`, `complex64`) or a new *shape model*
(ragged, static-rank) requires a one-line addition to `impedance/dtype.py` / `impedance/shape.py` —
the only case "add a library = one file" does not cover, and a deliberate one (a shared tag must live
in the core to bridge).

## The toy demo

`demo/pipeline.py` is a five-library straight line — `torch → numpy → scipy → jax_lower → jax` — that
distills where this project started (the spaCy/torch/numpy/jax `extract.py` tangle) into an
`embed → host-normalize → kernel → score` loop:

```python
def score(w: TorchMat, h: TorchMat) -> JaxPow2Vec:
    e   = torch.relu(torch.matmul(w, h))                  # torch    [4,8]·[8,4] -> [4,4]
    eh  = torch.export_host(e)                            # numpy    (real .cpu().numpy())
    nh  = scipy.softmax(eh, axis=-1)                      # scipy    over the host carrier
    kt  = jax_lower.as_pow2(bridge(host, jax_lower, nh))  # JaxLower [4,4] Pow2  (checked Dyn->Pow2)
    sym = jax_lower.add(kt, jax_lower.transpose(kt))      # JaxLower a Pow2 kernel op
    yj  = bridge(jax_lower, jax, sym)                     # jax      (real jnp.asarray)
    return jax.sum(jax.matmul(yj, yj), axis=-1)           # jax      [4]
```

Read it as a straight line: the four phantom params are inferred, each crossing is one named token,
and every device transfer / dtype handoff is named on the line where it happens. `demo/raw_pipeline.py`
computes the *identical value* as a pile of native calls — fully `mypy`-clean yet one edit from wrong
four ways — and `demo/mismatches.py` holds the deliberate crossings that do not build. See
[`ERGONOMICS.md`](ERGONOMICS.md) for the before/after.

```
python -m demo.pipeline        # the mediated pipeline
python -m demo.raw_pipeline    # the raw "before" (same numbers)
```

## What it does NOT give (the honest boundaries)

State these plainly so no one re-explains a guarantee the package does not make (ADR-0009 / ADR-0013):

- **Shape closure is KIND, not extent.** `Dyn`-vs-`Pow2` kind disagreement and non-pow2 *dim values*
  are construction-closed; **operand rank/extent agreement** (`[m,k]·[k,n]`) on `Dyn` adapters is a
  **runtime** error, not type-carried (the named stop — full dependent-shape typing forecloses none
  of the named impedances and would make the demo unreadable). Of the four axes, shape's headline is
  honored least; it is honored for shape-*kind*.
- **A genuinely new dtype / shape-model is a core edit.** Parametric cleanly over lib/device/
  capability; the dtype and shape-kind vocabularies are shared core enums (see the caveat above).
- **The host spine cannot express a direct device→device bridge.** A cupy-GPU → torch-GPU move
  round-trips through the host buffer by signature — the deliberate O(1) interchange choice; dlpack
  zero-copy is an adapter implementation detail behind the two-op interface, not a typed direct edge.
- **The in-library co-residence diagnostic reads as `[misc] Cannot infer`,** not a clean
  `[arg-type]` — a symmetric invariant-`TypeVar` conflict mypy cannot attribute to one operand. It
  blocks correctly; the message is just cryptic. The primary device closure (the host crossing) reads
  cleanly. (`demo/mismatches.py` (h) demonstrates and tests it.)
- **`_wrap` and `numpy.to_device` are disclosed reflection/relabel residue.** `from impedance.tensor
  import _wrap` can mint any tensor (the exact symmetric status of `pow2()` bypassing validation);
  the *public* surface is closed. The guarantee is "no *accidental* impedance," not "no impedance
  under deliberate reflection."

## Status / hygiene

`mypy --strict` clean (15 source files), `pytest` green (21 tests), jax/jaxlib pinned **0.10.1**. The
core imports no numerical library; each adapter imports exactly its own, lazily. Standalone — runs and
tests green with zero reference to any parent project, designed to be extracted to its own repository.
License: The Unlicense.
```
.
├── DESIGN.md            the settled design + the §8 post-critique revision (the SSOT)
├── README.md            this file
├── ERGONOMICS.md        the before/after
├── impedance/
│   ├── tensor.py        the opaque carrier Tensor[L,Dev,D,S]
│   ├── dtype.py shape.py the shared dtype tags + shape kinds (core enums)
│   ├── adapter.py       the STANDARDIZED seam Protocol LibAdapter[Lib,HDev,DevBase]
│   ├── host.py          the numpy host interchange + the O(1) bridge spine
│   └── lib/             one file per library — adding a library is adding one here
│       ├── numpy_lib.py torch_lib.py jax_lib.py
│       ├── jax_lower_lib.py   (nla_lab/lower lifted to one adapter — the Pow2 kernel adapter)
│       └── scipy_lib.py sklearn_lib.py  (host-family capability surfaces)
├── demo/                pipeline.py · raw_pipeline.py · mismatches.py
└── tests/
```
