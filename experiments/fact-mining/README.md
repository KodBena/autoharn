# fact-mining (spaCy experiments)

First pass at mining *facts in different logics* out of plain-text books
(`/home/bork/pg/pg78966.txt` — Singer, *A Short History of Medicine*). See the
header of `extract.py` for how each output family maps to a target logic
(SVO triples → classical fact base; entities → constants/sorts; dates →
temporal logic).

## Environment

Use the shared venv (do **not** make a per-project one):

    . ~/w/vdc/venvs/generic/bin/activate

Installed there: `spacy` 3.8, `en_core_web_sm`, `en_core_web_trf`,
`spacy-transformers`, `pyzmq`.

## Local extraction

    python extract.py /home/bork/pg/pg78966.txt --max-sents 60            # sm (fast, noisy)
    python extract.py /home/bork/pg/pg78966.txt --model en_core_web_trf   # trf (accurate, slow on CPU)
    python extract.py --help                                             # lists models + sizes

## GPU daemon (host) + remote client (guest)

The transformer model is slow on CPU. Run it on the VM **host** (GPU) as a
daemon; the guest talks to it over ZMQ. The wire carries **data only** —
JSON requests, spaCy `DocBin` (msgpack) replies — never pickle/code.

Host install (pick `cuda12x`/`cuda11x` to match the driver):

    pip install pyzmq 'spacy[cuda12x]' spacy-transformers
    python -m spacy download en_core_web_trf
    pip install torch --index-url https://download.pytorch.org/whl/cu124

Run the daemon on the host:

    python nlp_server.py --addr tcp://0.0.0.0:5599 --model en_core_web_trf --gpu

From the guest, either use the client directly or point the extractor at it:

    python nlp_client.py --addr tcp://192.168.122.1:5599        # smoke test (ping/info/parse)
    python extract.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599

### Coreference on the daemon (maverick-coref, host-only)

The daemon answers `{"coref": true}` by running **maverick-coref** and returning
char-offset clusters in the reply meta; the client attaches them to each `Doc` as
`doc._.coref_clusters` (the SAME attribute fastcoref used), so `resolve.py`
consumes host coref with no change. Load with daemon coref:

    python load_facts.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 --coref

#### Two coref paths: serial (reference) vs batched (default, fast)

maverick runs `predict()` once per paragraph (~200 sequential GPU calls, power-
cycling the PCIe GPU each time). Its *clustering* tail genuinely cannot tensor-
batch (`model_mes.py` does per-document `mention_idxs = mention_idxs[0]`), but its
**deberta encoder is fully batchable**. So the daemon has two coref code paths,
selected by `coref_mode` on the request (and by load_facts flags):

| path | `coref_mode` | how |
|------|--------------|-----|
| **serial** (reference) | `"serial"` | `Server.coref_clusters` — one `predict()` per text. Untouched ground truth. |
| **batched** (default)  | `"batched"`| `Server.coref_clusters_batched` — pad all paragraphs, run `model.encoder` **once** over B×S, then serve each item's precomputed hidden-state slice into maverick's **unchanged** per-doc clustering tail (the encoder is temporarily swapped for a stand-in; restored in `finally`). |
| **verify** | `"verify"` | run BOTH, load the trusted serial clusters, and return a pass/fail `coref_verify` diff. |

The batched path keeps everything fp32 (no `.half()` — that is a separate
decision) and only the deberta encoder is shared; the mention-extraction and
clustering math is maverick's own code on per-document hidden states, so outputs
stay faithful to serial.

**Fidelity story — run `--coref-verify` once before trusting batched.**

    # one-time check: runs serial AND batched, asserts clusters match, loads serial
    python load_facts.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 \
        --coref --coref-verify

    # normal fast run (batched encoder, the default under --coref):
    python load_facts.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 --coref

    # force the serial reference path (slow):
    python load_facts.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 \
        --coref --coref-serial

Comparison is **exact set equality** of clusters per paragraph (cluster order,
within-cluster mention order, and list-vs-tuple are all normalised away). Cluster
endpoints are integer *char* offsets, so there is no float slack to absorb at this
layer. The one fidelity caveat is upstream: batched matmul + right-padding can
make the encoder's hidden states differ from the serial run at the ~1e-5 level. In
principle a value sitting within ~1e-5 of a `sigmoid>0.5` mention threshold or an
antecedent `argmax` tie could flip, which *would* change the cluster set — and
that is exactly the event exact-set verify surfaces as a `FAIL` with a per-
paragraph `serial=… batched=…` diff. (padding is masked out by the attention mask,
so in practice the rows match and verify passes; the verify gate is the proof, not
an assumption.) `--coref-verify` loads the **serial** clusters either way, so a
verify run is also a safe run.

> Cannot be exercised on this guest (no maverick/CUDA). Implemented and AST/device-
> gate-clean here; **ready for host verification** via the commands above.

The full guest-side wire path is verified (client attach → resolve → pronoun
resolves). Host-side notes:
  * `Maverick(device="cuda"|"cpu")` — confirmed on the host.
  * PyTorch ≥2.6 defaults `torch.load(weights_only=True)`, which rejects the
    checkpoint's omegaconf globals; `coref()` forces `weights_only=False` (trusted
    official checkpoint) only during model construction.
  * download stalls at 0% are the HF Xet backend — fetch with `HF_HUB_DISABLE_XET=1`.
  * `coref_clusters()` reads `pred["clusters_char_offsets"]`; `resolve._char_span`
    tolerates inclusive-vs-exclusive end offsets (tries `e` then `e+1`) — still to
    confirm once a parse returns real clusters.

`RemoteNLP` in `nlp_client.py` is a near-drop-in for a loaded `nlp`:
`.pipe(texts)` / `nlp(text)` return real `Doc` objects rehydrated from DocBin,
so guest-side extraction code is unchanged whether the model is local or remote.

### Stage 1a — maverick's decode tail as a pure-JAX core (host-verified)

The batched path above still runs maverick's *torch* mention-extraction +
clustering tail per document. Stage 1a ports **that tail** to JAX, split the way
ADR-0012 P9 prescribes:

* **`jax_decode.py`** — the pure, total **device core**: three `@jax.jit` stages
  (start keep-mask, span keep-mask, coref-logits→no_ant→argmax) that mirror
  maverick `model_mes.py` line-for-line (the load-bearing start/end SWAP, the
  4-term bilinear, `tril().fill_diagonal_(0)`, and the `sigmoid(x)>0.5 ⇔ x>0`
  identity). It imports **jax + stdlib only** — never numpy.
* **`coref_host_shell.py`** — the thin imperative **host shell** for the
  irreducibly data-dependent glue jax can't trace inside a `jit` (the
  `torch.nonzero`-shaped index extraction, the O(K²) category-mask set logic, the
  sequential union-find, the bpe→token offset map). It is the **single jax
  host↔device home**: every `jax.device_get` (pull) and `jnp.asarray(host_data)`
  (lift) carries an inline `# host-device-boundary:` marker, enforced by
  `test_device_transfers.py`.

**Two-tier fidelity (ADR-0009).** Float logits are *not* required to match torch
bit-for-bit (different matmul / GELU / LayerNorm kernels); the **discrete cluster
set** is the invariant that must match exactly. `test_jax_decode_fidelity.py` is
the falsifier: it replays captured maverick fixtures through the JAX core and
asserts order-independent cluster-set equality — for **both** `singletons=False`
and the `singletons=True` decode branch — with non-vacuity guards (it fails, not
silently passes, if the fixtures yield no clusters / no ≥2-mention cluster / no
singleton).

**Guest-runnable gates (no jax/maverick needed), pure `ast`:**

    python test_device_transfers.py    # device-edge ops are single-homed + marked
    python test_import_xor.py          # no file imports both host (numpy) and device libs
    # or: pytest test_device_transfers.py test_import_xor.py

**HOST steps (where maverick + torch + CUDA live).** Capture the fixtures once,
then run the fidelity proof:

    . ~/w/vdc/venvs/generic/bin/activate     # + a host env with jax/maverick/CUDA

    # 1. capture decode-tail fixtures from maverick (defaults: N=6 paragraphs,
    #    OUTDIR=./fixtures). Dumps lhs/eos_mask/weights + maverick's clusters for
    #    BOTH singletons=False and singletons=True.
    python capture_fixtures.py            # or: python capture_fixtures.py 8 ./fixtures

    # 2. prove the pure-JAX tail == maverick on the captured cluster sets.
    pytest test_jax_decode_fidelity.py    # or: python test_jax_decode_fidelity.py

> Cannot be exercised on this guest (no jax/maverick/CUDA). The pure-`ast` gates
> above are green here; the fidelity test self-skips until fixtures exist on the
> host. Not yet wired into `nlp_server.py` — Stage 1a is the verified core, the
> production swap is the next step.

## Caching (redis)

Parsing is the expensive step; the result for a given `(model, config, text)` is
deterministic, so we cache it. `nlp_cache.py` stores DocBin bytes in redis,
keyed by a content hash. The cache lives on the **guest**, in front of the
daemon — a hit avoids the GPU round-trip entirely.

    python extract.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 --cache

**Which redis instance (both on the guest, 127.0.0.1):**

| port | role        | policy              | use for the cache? |
|------|-------------|---------------------|--------------------|
| 6380 | `memcache`  | `allkeys-lru`, no persistence | **yes** — regenerable, evictable |
| 6379 | `qeubo`     | `noeviction`, disk-persisted  | **no** — durable system of record |

`--cache` defaults to `redis://127.0.0.1:6380/0`. Keys are namespaced
`autoharn:spacy:doc:*` (shared redis — avoid cross-project collisions).

Verified: cold run = all misses, warm run = all hits with **zero** daemon calls,
and rehydrated-from-cache facts are byte-identical to a fresh parse.

**Latency note.** First trf request includes CUDA warm-up (the ~6 s you saw).
For genuinely-new text the lever is batching: `extract.py` sends all cache-miss
paragraphs in one `pipe()` call → one wire round-trip, GPU batches internally.

## Storing facts (psql) — one base, several logics

`schema.sql` creates an **ephemeral** `mining` schema in the harness DB
(`psql -h 192.168.122.1 -d harness`). Wipe it any time with one statement:

    DROP SCHEMA mining CASCADE;

The base tables (`document` / `sentence` / `assertion` / `entity` / `temporal`)
are **logic-agnostic** — they record what was extracted and where from. Each
logic is then a view/query over that base:

| view / query                | logic                  | idea |
|-----------------------------|------------------------|------|
| `mining.fact_classical`     | classical/relational   | `pred(subj,obj)`, positive only |
| `WITH RECURSIVE` over edges | classical (inference)  | transitive closure → *derived* facts |
| `mining.assertion.negated`  | defeasible             | seam for overridable / negated claims |
| `mining.contradiction`      | paraconsistent         | same `(s,p,o)` asserted both ways |
| `mining.fact_temporal`      | temporal (valid-time)  | a fact + the time expression in its sentence |

Apply + load:

    psql -h 192.168.122.1 -d harness -f schema.sql
    python load_facts.py /home/bork/pg/pg78966.txt --cache --max-sents 200
    # with coreference (local fastcoref pipeline; entity-norm always on):
    python load_facts.py /home/bork/pg/pg78966.txt --coref --max-sents 600
    # or against the GPU daemon: ... --remote tcp://192.168.122.1:5599 --cache

## Resolution layer (`resolve.py`) — surfaces → constants

`resolve.resolver_for(doc)` turns a subject/object head token into the canonical
constant the logics join on, in three steps: **(1) coreference** (fastcoref) maps
a pronoun to its referent; **(2) entity normalization** clusters `the Greeks` /
`Greek` / `Greeks` → `greek` (determiner-strip, singularize, NER-aware); **(3)** an
unresolved pronoun yields *no* constant (the authorial `we` is not an entity).
`assertion.subj_key/obj_key` store the result; the views join on it.

This visibly cleaned the fact base (`start(greek, medicine)`, `deify(greek,
aesculapius)`) and the `WITH RECURSIVE` closure now traverses real constants
(`aristotle -[be]-> greek -[start]-> medicine`). It also exposed that the
*earlier* noisy chains were **spurious** — routed through an unresolved `we` hub
that step (3) now removes.

**Honest limits (remaining).** (1) **SVO depth** — copulas, coordination, and
relative clauses are only partly handled, so `have`/`be` are overloaded edges;
(2) **predicate sense** — no word-sense disambiguation, so distinct `have`
meanings collapse; (3) **representative choice** — the coref cluster head is a
heuristic (shortest entity-bearing mention), occasionally wrong. (1)/(2) are the
next frontier; trf parses (via the daemon) help (1).
