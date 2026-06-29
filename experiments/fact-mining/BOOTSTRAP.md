# BOOTSTRAP — deploying the unified jax-only coref daemon from scratch

A from-scratch operational runbook for the **unified jax-only coreference path**
(`--coref-backend jax-unified`): every runtime file, the command that produces it, where
it must live, and the launch + verify sequence. It is deliberately a *runbook* — for the
narrative of *why* (the staged torch→jax migration, the device-hygiene argument) see
[`README.md`](README.md) "Stage 1b-iii — the unified jax-only daemon", and for exact flag
lists run the tools with `--help` (this doc does not re-type facts the code owns — ADR-0005
Rule 1 / ADR-0012 P1).

The headline property this path delivers: the coref daemon runs the **whole** forward —
tokenize → encode → decode → clusters — in **one process that imports jax and NEVER torch,
transformers, huggingface_hub, or tokenizers**. It tokenizes with **raw sentencepiece** from
a **vendored `spm.model`**, so it needs no HuggingFace surface and no HF cache at runtime.

---

## 0. Topology (three roles, two hosts)

```
  client                 nlp_server (HOST)              jax daemon (HOST, torch-free)
  load_facts.py  ──5599──▶  nlp_server.py   ──5600──▶  coref_decode_server.py
  (guest or host)          spaCy + maverick            jax-only: spm + jax_deberta + decode
                           (reference / --coref-verify) (NO torch/transformers/hf at runtime)
```

* **`nlp_server.py`** — the client-facing NLP server (default `tcp://0.0.0.0:5599`). For
  `jax-unified` it relays **only text** to the jax daemon and folds the returned clusters
  into the facts. It is **torch-bearing** (spaCy-trf + maverick) because it also holds the
  **serial maverick reference** that `--coref-verify` diffs against.
* **`coref_decode_server.py`** — the **unified jax-only daemon** (default
  `tcp://0.0.0.0:5600`). Started with `--deberta-weights` it serves the `coref` op (text →
  clusters). It imports jax and never torch (`jax_only_guard` + `assert_torch_free`).
* **`load_facts.py`** — the client/driver. Runs on the guest (`--remote`) or the host.

`nlp_server` and the jax daemon are **separate processes** precisely so no single process
holds both torch and jax (ADR-0012 host-XOR-device). They may share one physical host/GPU;
cap XLA's arena so the daemon does not pre-grab the card from the torch encoder (below).

---

## 1. Prerequisites

* **The venv** (shared; do not make a per-project one):

  ```
  . ~/w/vdc/venvs/generic/bin/activate
  ```

  It provides spaCy 3.8 + `en_core_web_sm`, `sentencepiece` 0.2.1, `transformers` 4.53.2
  (guest tokenization reference only — the daemon does **not** import it), and jax. The
  `StandalonePreprocessor` auto-downloads the nltk `punkt`/`punkt_tab` sentence splitter on
  first use; on an offline host pre-seed it (`python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"`).

* **HOST-only for the *exports*:** `maverick` (maverick-coref) + torch + the fine-tuned
  checkpoint + CUDA. The two `fixtures/*.npz` and the `spm.model` are produced **here** and
  only here (the fine-tuned weights live nowhere else). The jax daemon then runs **without**
  any of these at runtime.

* **OpenSUSE notes.** `/tmp` is a small tmpfs (≈5 GB); the vanilla-deberta guest proof and
  the real export write ~1.7 GB npz — point `TMPDIR` at a roomier volume
  (`export TMPDIR=/home/<you>/.cache/tmp`) or you will hit `OSError: Disk quota exceeded` /
  an OOM `SIGKILL`. Redis (if you use `--cache`) is the guest's `127.0.0.1:6380` volatile-lru
  instance — see [`README.md`](README.md) "Caching (redis)".

---

## 2. Runtime files — the complete inventory

Three files in `fixtures/` are all the unified daemon loads at runtime. **No HF cache, no
torch, no maverick** is touched once these exist.

| File | What it is | Produced by (HOST) | Loaded by |
| --- | --- | --- | --- |
| `fixtures/weights.npz` | the **decode-tail** learned params (the 6 FC `RepresentationLayer`s + the 8 bilinear antecedent weights/biases) | `capture_fixtures.py` (`extract_weights`) | daemon `--weights` → `coref_host_shell.lift_params` |
| `fixtures/deberta_maverick.npz` | maverick's **fine-tuned deberta encoder** — every weight under its torch key + one `__cfg__<field>` per `DebertaCfg` field + a `__tokenizer__` identity | `export_deberta_maverick.py` (`save_npz`) | daemon `--deberta-weights` → `coref_host_shell.lift_deberta_params` / `build_deberta_cfg` |
| `fixtures/deberta_maverick.spm` | the **vendored sentencepiece model** (maverick's encoder sub-word model) — the tokenizer as a plain local file | `export_deberta_maverick.py` (`vendor_spm`, the npz's `.spm` sibling) | daemon → `StandalonePreprocessor.from_spm` (raw sentencepiece, no transformers) |

The `.spm` is the npz's **sibling**: `deberta_maverick.npz` → `deberta_maverick.spm`. That
one-line convention has a single home, `export_deberta_maverick.spm_sibling_path`, imported
by the daemon — so writer and reader cannot drift to two hand-typed paths (ADR-0012 P1). The
daemon **fails loud at startup** if the `.spm` sibling is missing (re-run the export).

### 2a. Produce the decode-tail weights (`weights.npz`)

```
. ~/w/vdc/venvs/generic/bin/activate
python capture_fixtures.py            # writes fixtures/weights.npz (+ per-paragraph fidelity fixtures)
```

`capture_fixtures.py` runs maverick **serially on CUDA** and dumps `weights.npz` once
(shared) plus `para_*.npz/json` fidelity fixtures (used by the decode-fidelity tests). For
the daemon you need only `weights.npz`. (HOST-only: maverick + torch + CUDA.)

### 2b. Produce the encoder weights + the vendored spm (`deberta_maverick.npz` + `.spm`)

```
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    python export_deberta_maverick.py --out ./fixtures/deberta_maverick.npz
```

This writes **both** `fixtures/deberta_maverick.npz` **and** `fixtures/deberta_maverick.spm`
(it copies maverick's own `spm.model` — the exact sub-word model the encoder was trained
with — next to the weights). The export re-asserts the keyset bijection
(`set(converted) == jax_deberta.param_keys(cfg)`) and fails loud on any config/keyset
divergence. (HOST-only: maverick + torch.)

> **First-time host:** `export_deberta_maverick.py` does `Maverick(device="cpu")`, which
> fetches maverick's fine-tuned checkpoint from the Hub if it is not already cached. The
> `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` prefix above PROVES the export needs no network
> on an already-provisioned host — but on a genuinely from-scratch host whose maverick
> checkpoint is not yet cached, that offline fetch fails. **Drop the two OFFLINE vars for
> the first run** (let it populate the cache once), then keep them on for every subsequent
> offline-proof export.

> The fine-tuned weights are host-only, so **only the host** confirms the real export and
> its keyset bijection. The guest proves the npz round-trip on *vanilla* deberta and the
> full tokenization bit-identity (§5).

---

## 3. Launch — one command (recommended), or both daemons by hand

The stack is two daemons (the host-XOR-device split): the jax-only unified daemon (`:5600`)
and the torch/spaCy `nlp_server` (`:5599`). The **supervisor** brings up both in the right
order and stops both on `^C`:

```
python run_coref_stack.py --gpu
# defaults: ./fixtures/{weights,deberta_maverick}.npz ; host-ip 192.168.122.1 ; mem-fraction 0.3
```

It starts the decode daemon, **waits until it answers a ping** (so `nlp_server`'s warmup never
relays into a not-yet-listening socket), then starts `nlp_server` pointed at it
(`--coref-backend jax-unified --decode-addr …`), prefixes both logs (`[decode]`/`[nlp]`) onto
one console, and `^C` tears both down cleanly, in order. Knobs: `python run_coref_stack.py --help`.

**Or, by hand** — two terminals, for debugging one daemon in isolation:

```
# (1) the JAX daemon — jax-only, torch-free; --deberta-weights enables the unified `coref` op.
#     The .spm sibling and the tokenizer identity come FROM the export; no --coref-model needed.
XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
    python coref_decode_server.py --addr tcp://0.0.0.0:5600 \
        --weights ./fixtures/weights.npz \
        --deberta-weights ./fixtures/deberta_maverick.npz

# (2) the front-end nlp_server — relays text to the daemon for jax-unified coref.
python nlp_server.py --addr tcp://0.0.0.0:5599 --gpu \
    --coref-backend jax-unified --decode-addr tcp://127.0.0.1:5600
```

* `XLA_PYTHON_CLIENT_MEM_FRACTION=0.3` (or `XLA_PYTHON_CLIENT_PREALLOCATE=false`) caps the
  daemon's XLA arena so it shares the GPU with nlp_server's torch encoder; the daemon sets a
  conservative default if you set neither.
* The daemon prints `UNIFIED encode+decode (jax-only; torch-free)` and the tensor counts
  when the unified op is live. On startup it **fails loud** if any deberta tensor is
  missing/extra (load-time keyset gate) or the `.spm` sibling is absent.
* `--decode-addr` on `nlp_server` must point at the daemon's `--addr`. From a guest, use the
  host IP the wire reaches it on (the repo's default is `tcp://192.168.122.1:5600`).
* For exact flags: `python coref_decode_server.py --help`, `python nlp_server.py --help`.

---

## 4. End-to-end check — `--coref-verify`

The discrete-set falsifier (ADR-0009): run **both** the jax-unified daemon and the **serial
maverick reference** on the same paragraphs and diff the cluster sets. `n_mismatch == 0` over
the whole document means the unified torch-free forward reproduces maverick bit-for-bit.

```
python load_facts.py ./book.txt \
    --remote tcp://192.168.122.1:5599 \
    --coref --coref-backend jax-unified \
    --coref-verify                     # ONE url — --decode-addr is optional (nlp_server's default).
                                       # expect verify=PASS (0/N mismatches)
```

`nlp_server` runs `maverick.predict` (its own torch decode) and the jax-unified daemon for
each text and reports a `coref_verify = {ok, n_mismatch, n}` (printed as
`verify=PASS(0/N)`); `load_facts` loads the **trusted serial** clusters. Run this once before
trusting the fast path. (HOST authority: the serial reference is maverick on torch.)

A `--max-paras 5 --trace` run additionally proves the dense `eos_mask [S,S]` + `last_hidden_
state` wire is **structurally gone** — the only coref wire span is a tiny TEXT request — see
[`README.md`](README.md) "Stage 1b-iii".

---

## 5. What is HOST-only vs guest-provable

| Step | Where | Why |
| --- | --- | --- |
| `capture_fixtures.py` → `weights.npz` | **HOST** | maverick + torch + CUDA |
| `export_deberta_maverick.py` → `.npz` + `.spm` | **HOST** | maverick + the fine-tuned checkpoint live only here |
| `--coref-verify` (unified vs `maverick.predict`) | **HOST** | the serial reference is maverick on torch (the end-to-end cluster authority) |
| the jax daemon itself (`coref_decode_server.py`) | **HOST hardware, torch-free process** | runs on the host/GPU but imports jax and NEVER torch |
| **tokenization bit-identity** (sentencepiece vs the transformers reference, incl. >512 + byte-fallback + unicode) | **GUEST** | `transformers` is the reference, fully guest-runnable; no maverick/jax weights needed |
| the static gates + the torch-free / sys.modules proof | **GUEST** | pure-AST + a subprocess; no weights |

Guest-runnable gates (no jax/maverick weights needed):

```
python test_import_xor.py            # daemon files host-XOR-device (coref_decode_inputs is neither side)
python test_device_transfers.py      # the single jax home is coref_host_shell.py
python -m pytest test_preprocess_bit_identity.py   # sentencepiece == the fast tokenizer, bit-for-bit
python -m pytest test_torch_free_daemon.py::test_tokenizer_path_is_torch_and_hf_free  # sys.modules proof
#   COREF_REQUIRE_BIT_IDENTITY=1 MAVERICK_SRC=.../maverick_model.py makes the maverick-source
#   end-to-end falsifier a HARD requirement (else it skips when maverick source is absent).
#   test_torch_free_daemon::test_unified_forward_is_torch_free needs a ~1.7GB vanilla npz —
#   set TMPDIR to a roomy volume or it OOM/quota-fails on a small tmpfs.
```
