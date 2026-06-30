# Ergonomics — the before/after

The bar for `impedance` is type-sane **and** ergonomic: the mediated pipeline must read *more*
naturally than the raw library-call mess, not less. The verbosity of the four phantom params lives in
the adapter definitions (written once), never in the pipeline (read often) — every phantom param is
inferred, every crossing is one named token. This is the judgement the maintainer makes by reading
the demo; here is the side-by-side.

## Before — `demo/raw_pipeline.py` (the native-call mess)

```python
def raw_score(w: torch.Tensor, h: torch.Tensor) -> JaxArray:
    e = torch.relu(torch.matmul(w, h))
    if e.is_cuda:                                 # 1. manual device juggle — easy to forget
        e = e.cpu()
    eh: npt.NDArray[np.float32] = e.detach().cpu().numpy()
    eh = eh.astype(np.float32)                    # 2. silent dtype coercion, papering a drift
    nh = special.softmax(eh, axis=-1).astype(np.float32)
    sym = nh + nh.T                               # 4. the kernel leg's pow2 need lives in your head
    yj = jnp.asarray(sym)                         # 3. bare cross-library handoff, no guard
    return jnp.sum(jnp.matmul(yj, yj), axis=-1)
```

This is **fully `mypy --strict`-clean** — and that is the indictment. The raw libraries do not encode
the `(lib, device, dtype, shape)` seam, so the type checker is blind to all four latent ways this is
one edit from being wrong:

1. **device** — `.detach().cpu().numpy()` works only because someone remembered the `.cpu()`; the
   `if e.is_cuda` juggle is the tell. Hand a CUDA tensor straight to `.numpy()` → a runtime crash.
2. **dtype** — the `.astype(np.float32)` papers over a possible `float64` drift; nothing forces it,
   and an upstream f64 flows to the jax matmul unnoticed.
3. **lib** — `jnp.asarray(sym)` is a bare handoff; pass a torch tensor here by mistake and mypy
   shrugs (its `*args` are `Any`-ish at the boundary).
4. **shape** — no kind is carried; the kernel leg's power-of-two requirement is invisible. A non-pow2
   extent is a runtime error far downstream.

## After — `demo/pipeline.py` (the mediated ACL)

```python
def score(w: TorchMat, h: TorchMat) -> JaxPow2Vec:
    e   = torch.relu(torch.matmul(w, h))                  # Tensor[Torch,    TorchCPU, F32, Dyn]
    eh  = torch.export_host(e)                            # Tensor[Numpy,    Host,     F32, Dyn]
    nh  = scipy.softmax(eh, axis=-1)                      # scipy over the host carrier — stays host
    kt  = jax_lower.as_pow2(bridge(host, jax_lower, nh))  # Tensor[JaxLower, JaxCPU,   F32, Pow2]
    sym = jax_lower.add(kt, jax_lower.transpose(kt))      # Tensor[JaxLower, JaxCPU,   F32, Pow2]
    yj  = bridge(jax_lower, jax, sym)                     # Tensor[Jax,      JaxCPU,   F32, Pow2]
    return jax.sum(jax.matmul(yj, yj), axis=-1)           # Tensor[Jax,      JaxCPU,   F32, Pow2]
```

Same value, computed identically (parity-tested, bit-equal). But it **cannot be written wrong in any
of the four ways** — and it reads as a straight line:

- **The happy path has no ceremony.** A correct crossing is one token (`torch.export_host(e)`); no
  per-call config, no context manager, no explicit type argument on the hot line.
- **Inference carries the verbosity.** The four phantom params are inferred; the full `Tensor[L,Dev,
  D,S]` appears only in the comments (shown for the reader) and in adapter definitions (authored once).
- **Adapters read as library handles.** `torch.matmul(...)`, `scipy.softmax(...)`,
  `jax.import_host(...)` read like the libraries they mediate; the crossing ops have the *same* names
  on every adapter (`export_host` / `import_host` / `to_device` / `cast` / `brand`) — learn the seam
  once, it is the same for torch as for jax.
- **The errors are early and legible.** A wrong crossing is a `mypy --strict` `[arg-type]` /
  `[type-var]` / `[attr-defined]` naming both the offending and the expected `Tensor[…]` — the
  diagnostic *is* the four-axis story ("Torch where Jax expected", "F64 where F32 required").

## The five crossings that do not build (`demo/mismatches.py`)

Each is a few lines, each a real `mypy --strict` error at a library crossing, each regression-tested:

| crossing | the illegal line | diagnostic |
| — | — | — |
| device (host) | `torch.export_host(cuda_tensor)` | `[arg-type]` — `TorchCUDA` ≠ host-side `TorchCPU` |
| lib | `jax.matmul(torch_tensor, y)` | `[arg-type]` — `Torch` ≠ `Jax` |
| dtype | `jax.matmul(f64_a, f64_b)` | `[arg-type]` — `F64` ≠ `F32` |
| shape | `jax_lower.zeros(127, 8, F32)` | `[arg-type]` — `int` ≠ `Pow2Dim` (and `pow2(127)` raises) |
| capability | `jax_lower.gather(y)` | `[attr-defined]` — the lowerable adapter has no `gather` |
| device (model) | `torch.to_device(x, JaxGPU)` | `[type-var]` — a jax device is not a `TorchDevice` |
| device (model) | `torch.brand(raw, dev=JaxCPU, …)` | `[type-var]` — closed at entry too |
| device (co-residence) | `torch.matmul(cpu, cuda)` | `[misc]` — operand `Dev` cannot unify |

## Friction, named honestly

Ergonomics is a pass *for the demonstrated path*, with friction worth stating rather than hiding:

- **device/dtype are passed as bare class objects** (`dev=TorchCPU, dt=F32`) — reads slightly unusual
  versus a string or enum, the price of using the tag classes as phantom carriers.
- **the co-residence error reads cryptically** (`[misc] Cannot infer _Dev`) rather than naming the
  device violation — a mypy limitation on symmetric invariant-`TypeVar` conflict (see README). It
  blocks correctly; it just does not read as "device mismatch."
- **a numpy-origin entry into a device adapter is a two-step nest** (`jax.import_host(host.brand(...))`)
  — there is no single `jax.from_numpy`; the bridge spine is two named ops by design (O(1) per library).

None of these weakens a closure; they are the true reading of the ergonomic bar, stated so the
maintainer judges the real surface, not a polished one.
