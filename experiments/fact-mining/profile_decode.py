#!/usr/bin/env python
"""Profile the pure-JAX decode stages and emit a Perfetto-loadable trace.

Run ON THE HOST (the GPU + fixtures/weights.npz live there):

    python profile_decode.py --logdir /tmp/jaxprof --reps 40

It profiles the THREE jit'd stages the decode forward pass is built from — the same
`mention_start_keep` / `span_mention_keep` / `coref_decode` you saw in
docs/decode_forward — with synthetic inputs of representative shape. Input *values*
don't change the XLA graph, so the kernels and dispatch you see are the real ones; the
weights are the real decode-tail params, so the shapes are exact.

It prints the path to a `*.trace.json.gz`. Open https://ui.perfetto.dev and drag-drop
that file (no TensorBoard needed — jax writes the Chrome/Perfetto trace format directly).

What to look for in Perfetto:
  * the host (CPU) track shows TraceMe regions named after the XLA executables — one per
    jit stage per rep; the GAP between "dispatch" and the device kernel is the pjit/XLA
    dispatch floor (the fixed per-call cost the decode is dominated by at these tiny sizes).
  * on a GPU host, a device/stream track shows the actual CUDA kernels (the einsums,
    the FC matmuls). Their summed duration is the real compute; everything else is overhead.
"""
from __future__ import annotations

import argparse
import glob

import numpy as np

import jax
import jax.numpy as jnp

import jax_decode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", default="fixtures/weights.npz",
                    help="decode-tail weights .npz (default %(default)s)")
    ap.add_argument("--logdir", default="/tmp/jaxprof", help="trace output dir")
    ap.add_argument("--reps", type=int, default=40, help="traced iterations")
    ap.add_argument("--S", type=int, default=160, help="sequence length (subtokens)")
    ap.add_argument("--K", type=int, default=24, help="#mentions")
    ap.add_argument("--P", type=int, default=48, help="#candidate (start,end) pairs")
    a = ap.parse_args()

    with np.load(a.weights) as z:
        params = {k: jnp.asarray(z[k], dtype=jnp.float32) for k in z.files}

    # TH (encoder hidden) = the in-dim of the first lhs-consuming classifier.
    th_key = next((k for k in params if k.endswith("start_token_classifier.dense1.weight")), None)
    if th_key is None:
        raise SystemExit("can't find start_token_classifier.dense1.weight; available keys:\n  "
                         + "\n  ".join(sorted(params)))
    TH = int(params[th_key].shape[1])
    print(f"device={jax.devices()[0]}  TH={TH}  S={a.S} K={a.K} P={a.P}  reps={a.reps}", flush=True)

    key = jax.random.PRNGKey(0)
    lhs = jax.random.normal(key, (a.S, TH), jnp.float32)
    ps = (jnp.arange(a.P) % a.S).astype(jnp.int32)
    pe = ((jnp.arange(a.P) + 1) % a.S).astype(jnp.int32)
    start_reps = jax.random.normal(key, (a.K, TH), jnp.float32)
    end_reps = jax.random.normal(key, (a.K, TH), jnp.float32)
    cmasks = jnp.ones((jax_decode.NUM_CATS, a.K, a.K), jnp.float32)

    def one_decode() -> None:
        # the three stages, each named so the regions are legible in Perfetto.
        with jax.profiler.TraceAnnotation("stage1_mention_start_keep"):
            jax_decode.mention_start_keep(params, lhs).block_until_ready()
        with jax.profiler.TraceAnnotation("stage2_span_mention_keep"):
            jax_decode.span_mention_keep(params, lhs, ps, pe).block_until_ready()
        with jax.profiler.TraceAnnotation("stage3_coref_decode"):
            jax_decode.coref_decode(params, start_reps, end_reps, cmasks).block_until_ready()

    one_decode()  # warm: compile now so the TRACE is steady-state, not the cold compile
    with jax.profiler.trace(a.logdir):
        for _ in range(a.reps):
            one_decode()

    hits = sorted(glob.glob(a.logdir + "/**/*.trace.json.gz", recursive=True))
    print("\nPerfetto trace(s) written:", flush=True)
    for h in hits:
        print("   ", h)
    print("\nOpen https://ui.perfetto.dev  ->  'Open trace file'  ->  the .trace.json.gz above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
