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
daemon; the guest talks to it over ZMQ. The wire carries **data only** — JSON
requests and JSON or `DocBin`(msgpack) replies — never pickle/code.

### Wire protocol (request `format` picks the reply shape)

The request is always JSON (`{"op":"parse","texts":[...],"format":..., "coref":...}`).
The `format` field selects what comes back — and, decisively, **what the client must
import**:

| `format` | reply | client imports | used by |
|----------|-------|----------------|---------|
| **`facts`** (the lean default for `load_facts --remote`) | one JSON frame: `{ok, format:"facts", n, model, lang, facts:[<FactBundle>, ...]}` | **json + zmq + psycopg only** — never torch/spaCy/transformers | `RemoteNLP.pipe_facts` → `load_facts` |
| `docbin` | JSON meta frame + a `DocBin`(msgpack) binary frame of real `Doc`s | spaCy (lazy, in `.pipe()`) to rehydrate | `RemoteNLP.pipe` → `extract.py` demo |
| `json` | one JSON frame of token-level `doc_to_json` dicts | json only | diagnostics |

**The lean-client win (ADR-0011 — foreclosed, not just done).** The old `--remote`
client deserialized a `DocBin` and walked the `Doc` on the **guest**, so every
invocation paid a cold ML-stack import — `import spacy` drags `thinc → torch`
(+`transformers`) — *~1.77s on the guest (and it pulls torch), ~4.4s cold on the host
stack* — purely to read a reply the GPU had already finished. There is **no** lean
spaCy import (`from spacy.tokens import DocBin` alone still pulls torch
unconditionally), so the only fix is structural: on the `facts` path the **daemon**
runs the SSOT extractor (`extract.doc_to_facts`) host-side and ships finished JSON
`FactBundle` records; the client imports **only json + zmq + psycopg** (**~0.21s**,
torch never loaded). The facts are discrete records (strings + int offsets), so JSON
is **bit-exact** for them (ADR-0009 discrete-invariant) — `test_doc_to_facts_equivalence.py`
pins OLD-inline == `doc_to_facts` + JSON round-trip set-for-set. The lard is held out
by the foreclosing gate `test_lean_remote_client.py`: a fresh-subprocess probe drives
`import load_facts` + `RemoteNLP` + a facts request + the `--remote --cache` wrapper
(`FactCache`/`CachingFacts`) and **fails** if any of torch/spaCy/transformers/thinc
lands in `sys.modules` (with a prepended-`import spacy` self-check proving it has
teeth). `doc_to_facts` is the **single home** for "what a fact is" (ADR-0012 P1): the
daemon and the local non-remote path are its two callers; the `FactBundle` /
`*Record` `TypedDict`s in `extract.py` are the wire's one typed authority (P7/P8).

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

The daemon answers `{"coref": true}` by running **maverick-coref** and producing
char-offset clusters. On the **`facts`** path the daemon attaches them **host-side**
(right before `doc_to_facts`) so the lean client never touches a `Doc`; on the
`docbin` path they ride the reply meta and the client attaches them. Either way the
wire payload is decoded by the **one** decoder `resolve.attach_coref_clusters(doc,
clusters)` — the same function on both sides — onto `doc._.coref_clusters` (the SAME
attribute fastcoref used), so `resolve.py` consumes host coref with no change and the
two paths cannot drift on the cluster encoding. Load with daemon coref:

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

`RemoteNLP` in `nlp_client.py` has two surfaces. `.pipe_facts(texts)` is the lean
default — finished JSON `FactBundle`s, no spaCy on the client (the `facts` wire
above). `.pipe(texts)` / `nlp(text)` return real `Doc` objects rehydrated from a
`DocBin` (spaCy lazy-imported only there), so the demo extraction code in `extract.py`
is unchanged whether the model is local or remote — but importing `nlp_client` and
using the facts wire stays torch/spaCy-free.

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

### Stage 1b-i — the pure-JAX decode tail behind a ZMQ daemon (over the wire)

Stage 1a proved the JAX decode tail *in process*. Stage 1b-i puts that **same,
unmodified** core behind a ZMQ REP daemon so the production encoder can ship one
document's decode-tail intermediates over the wire and get cluster offsets back —
without re-implementing one line of decode math (ADR-0012 P9 / P1: a thin shell
that **calls** `coref_host_shell.decode_document`, nothing else).

* **`coref_decode_server.py`** — the daemon and the **wire↔device boundary**. It
  loads the decode-tail weights into jax arrays **once** at startup, and per
  request lifts the wire `last_hidden_state` onto the device and calls the proven
  shell. It is a *second, distinct* jax host↔device edge (the wire seam — the
  pipeline edge stays in `coref_host_shell.py`), declared in **both** gates
  (`test_import_xor.BOUNDARY_FILES` and `test_device_transfers.HOMES["jax"]`); both
  `jnp.asarray` lifts carry an inline `# host-device-boundary:` marker. Its name is
  neutral (not `jax_*`), so the honest-filename rule lets it hold the numpy↔jax mix.
* **`coref_decode_client.py`** — **host-only** (numpy, no device lib). Packs `lhs`
  as **raw little-endian float32 bytes** (`'<f4'`) and coerces the structural maps
  to JSON-native types, so a real tokenizer's `numpy.int64`/`None` maps serialize
  cleanly.

**Why raw float32 bytes (the bit-exactness claim).** JSON-decimal floats route
every value through a float64 decimal round-trip and can flip the last mantissa
bit — exactly the kind of perturbation that can flip a `sigmoid>0.5` / `argmax`
decision near a boundary (ADR-0009's residual risk). So `last_hidden_state` rides
the wire as raw IEEE-754 `'<f4'` bytes (one JSON meta frame + one binary frame),
**bit-identical** end to end; structural inputs are integers/strings (JSON-exact)
and the returned offsets are integers (JSON-exact). **No `send_pyobj`/pickle** —
data only, mirroring `nlp_server.py`/`nlp_client.py`.

**Over-the-wire fidelity (ADR-0013).** `test_decode_daemon_fidelity.py` starts the
real daemon as a subprocess and decodes every fixture **through ZMQ**, asserting
the cluster sets equal maverick's captured `clusters_token_offsets` (for both
`singletons` flags, with the same non-vacuity guards as Stage 1a). Two pure units
back it without a daemon: `test_lhs_wire_roundtrip_is_bit_exact` (pack→unpack is
byte-identical) and `test_unpack_lhs_fails_loud_on_bad_wire` (a truncated / wrong-
dtype / non-2D blob raises, never silently coerces — ADR-0002).

**Guest-runnable gates (pure `ast`, no jax/maverick):**

    python test_device_transfers.py    # both jax homes (pipeline + wire seam) single-homed + marked
    python test_import_xor.py          # coref_decode_server.py is the one declared host↔device boundary
    # or: pytest test_device_transfers.py test_import_xor.py

**HOST steps (where jax + maverick + CUDA live).** Capture the Stage-1a fixtures
once (they double as the daemon's inputs + `weights.npz`), start the daemon, then
run the over-the-wire proof. Use **`python -m pytest`**, never bare `pytest` — on
this host the `pytest` console script dispatches to an interpreter without jax and
would falsely "skip":

    . ~/w/vdc/venvs/generic/bin/activate     # + a host env with jax/maverick/CUDA

    # 1. capture fixtures (if not already done for Stage 1a):
    python capture_fixtures.py               # writes ./fixtures/para_*.{npz,json} + weights.npz

    # 2. start the decode daemon (cap XLA's arena so it co-resides politely with torch):
    XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
        python coref_decode_server.py --addr tcp://0.0.0.0:5600 --weights ./fixtures/weights.npz

    # 3. in another shell, run the over-the-wire fidelity test (it starts its OWN
    #    daemon subprocess on a loopback port, so step 2 is only for manual smoke-testing):
    python -m pytest test_decode_daemon_fidelity.py
    # smoke-test a running daemon by hand:
    python coref_decode_client.py --addr tcp://192.168.122.1:5600   # ping / info

> Cannot be exercised on this guest (no jax/maverick/CUDA). The pure-`ast` gates
> and the two pure wire units are green here; the daemon fidelity test self-skips
> until fixtures + jax exist on the host. The production encoder→daemon hand-off is
> wired in **Stage 1b-ii** below.

### Stage 1b-ii — the live encoder→daemon hand-off (`--coref-backend jax-daemon`)

Stage 1b-i proved the daemon's decode equals maverick's **captured** clusters when
*replaying fixtures*. Stage 1b-ii wires the daemon into the **live** path: the
production torch encoder in `nlp_server.py` ships each paragraph's decode-tail
intermediates to the daemon and gets cluster offsets back — maverick's decode tail
**retired from the live path**, no fixtures involved.

* **`coref_decode_inputs.py`** — the **single source (ADR-0012 P1)** for maverick's
  FRONT-half prep. `prepare_decode_inputs(mav, text)` runs `preprocess` + `tokenize`
  (the deberta sub-word ids, `eos_mask`, `subtoken_map`, `new_token_map`, **and** the
  per-token `char_offsets`); `clusters_token_to_char_offsets(...)` is a verbatim
  mirror of maverick.predict's `clusters_char_offsets` (`char_offsets[start][0] ..
  char_offsets[end][1]`, inclusive end). It is **framework-free** (no torch/jax/numpy),
  so it trips neither gate. **All three** producers of that prep now call it — the
  fixture capture (`capture_fixtures.capture_one`), the live jax-daemon path, and the
  batched maverick path (`coref_clusters_batched`, which reads just `input_ids`/
  `attention_mask` off the result) — so the extraction cannot drift between them.
* **`nlp_server.encode_last_hidden_state(model, input_ids, attention_mask)`** — the
  **one torch device op** of this backend, kept in the torch home (markers + the
  device-transfer gate). Its encoder call is byte-identical to maverick's own forward,
  so on the same inputs `lhs` equals what `predict` computes internally. `nlp_server`
  authors **no** jax op: the decode is shipped to the daemon via the host-only
  `coref_decode_client.RemoteDecode`.
* **`Server.coref_clusters_jax_daemon(texts, decode_addr)`** — per paragraph:
  `prepare_decode_inputs` → `encode_last_hidden_state` → `RemoteDecode.decode(...,
  singletons=False)` → `clusters_token_to_char_offsets`. Serial (per-paragraph),
  matching the maverick reference; the point is to exercise the jax decode tail
  bit-for-bit, not to be fast.

**Routing.** `load_facts --coref-backend jax-daemon --decode-addr ...` → `RemoteNLP`
sets the request's `coref_backend`/`decode_addr` fields → `nlp_server.handle` overrides
its defaults per call → `_run_coref` dispatches to `coref_clusters_jax_daemon` →
`RemoteDecode.decode`. The default backend stays **`maverick`** (the reference, its own
decode tail); `--coref-mode verify` runs the trusted serial maverick reference too and
reports a pass/fail fidelity diff against whichever backend is selected.

**Live-wire fidelity (`test_livewire_fidelity.py`).** Drives the FULL live path on
freshly-loaded maverick and asserts both the token- and char-offset cluster **sets**
equal maverick's own `predict(text)`, bit-for-bit (ADR-0009). The char clusters are
produced by driving the **actual** `Server._run_coref(..., "jax-daemon", ...)` →
`coref_clusters_jax_daemon` (wired to the test's maverick + daemon via `Server.__new__`
+ preset `_coref`/`_decoders`), so the live orchestration and backend dispatch are
certified, not a parallel copy; the token offsets are decoded once more at the leaf for
the most sensitive bit-exact probe (the server surfaces only char spans). Daemon weights
are extracted from the very model we encode with (no fixture dependency). The same
non-vacuity guard as the other fidelity proofs (≥1 cluster, ≥1 with ≥2 mentions).

**Guest-runnable gates (pure `ast`, no jax/maverick):**

    python test_device_transfers.py    # encode_last_hidden_state's torch ops single-homed + marked
    python test_import_xor.py          # coref_decode_inputs.py is framework-free (host=[] device=[])

**HOST steps (where jax + maverick + CUDA live).** Use **`python -m pytest`**, never
bare `pytest` — on this host the `pytest` console script dispatches to an interpreter
without jax and would falsely "skip":

    . ~/w/vdc/venvs/generic/bin/activate     # + a host env with jax/maverick/CUDA

    # 1. start the JAX decode daemon (cap XLA's arena so it co-resides politely with
    #    torch on the same card). Weights come from the Stage-1a fixture capture:
    XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
        python coref_decode_server.py --addr tcp://0.0.0.0:5600 --weights ./fixtures/weights.npz

    # 2. run the live-wire fidelity test (it starts its OWN daemon subprocess on a
    #    loopback port with weights from the live model, so step 1 is only for the
    #    load_facts run below / manual smoke-testing). On a small card, set
    #    MAVERICK_DEVICE=cpu to encode on CPU and leave the GPU to the daemon:
    python -m pytest test_livewire_fidelity.py

    # 3. run the normal extraction selecting the jax-daemon backend (the live
    #    encoder→daemon hand-off). The spaCy/maverick daemon must be running too
    #    (`python nlp_server.py --addr tcp://0.0.0.0:5599 --model en_core_web_trf
    #    --gpu`, from the "GPU daemon" section). --remote is that spaCy daemon;
    #    --decode-addr is the JAX decode daemon from step 1 (passed through to it):
    python load_facts.py ./book.txt \
        --remote tcp://192.168.122.1:5599 \
        --coref --coref-backend jax-daemon --decode-addr tcp://192.168.122.1:5600
    #    add --coref-verify to also run the serial maverick reference and emit a
    #    pass/fail fidelity diff against the jax-daemon clusters.

> Cannot be exercised on this guest (no jax/maverick/CUDA). The pure-`ast` gates are
> green here; `test_livewire_fidelity.py` self-skips (ModuleNotFoundError) until
> maverick/torch/jax exist on the host.

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

## Tracing the pipeline (`--trace`) — where the ~22s goes, who blocks on whom

A distributed-span tracer (`spans.py`, SSOT) stitches all **three** processes —
the guest client (`load_facts`), the host spaCy daemon (`nlp_server`), and the host
JAX decode daemon (`coref_decode_server`) — into **one** trace. It is **OFF by
default**: untraced, `span()` returns a shared no-op (no DB, no allocation) and the
wire is untouched, so tracing never distorts the time it measures. The trace context
rides *inside* the existing ZMQ JSON meta on both wires, so each receiver parents its
spans under the sender's blocked (`zmq_wait`) span.

Spans land in an **ephemeral** `trace` schema (separate from `mining`), wiped with
one statement: `DROP SCHEMA trace CASCADE;`. Apply it once:

    psql -h 192.168.122.1 -d harness -f trace_schema.sql

**Capture a traced pass** (host: both daemons in the jax env; guest: the client).
Add `--trace` to any normal `load_facts` invocation; it mints a code-stamped
`trace.run` (git commit/tree incl. uncommitted edits + exact cmd + config) and turns
tracing on across both wires:

    # host — spaCy daemon (GPU) routing coref to the JAX decode daemon
    python nlp_server.py --addr tcp://0.0.0.0:5599 --gpu \
        --coref-backend jax-daemon --decode-addr tcp://127.0.0.1:5600
    # host — JAX decode daemon
    XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
        python coref_decode_server.py --addr tcp://0.0.0.0:5600 --weights ./fixtures/weights.npz

    # guest — traced load through both wires
    python load_facts.py /home/bork/pg/pg78966.txt \
        --remote tcp://192.168.122.1:5599 --coref --coref-backend jax-daemon \
        --max-paras 5 --trace
    # prints: === trace: run_id=N | K client span(s) flushed to the `trace` schema ===

Clock note: `dur_ms` is a **monotonic, per-process** duration (skew-immune — use it
for "how long did X take"); `t_start`/`t_end` are **wall-clock** and exist only for
**cross-process ordering** (guest↔host clocks may be skewed). Never subtract a wall
time in one process from one in another.

**Read the timeline** (the latest run, indented by depth — the cross-process tree
`client.run → client.zmq_wait → nlp_server.handle → {parse, coref} → nlp_server.zmq_wait.decode → decode_server.handle → jax_decode`):

    psql -h 192.168.122.1 -d harness -c "
    WITH RECURSIVE t AS (
      SELECT span_id, process, name, dur_ms, t_start, 0 AS depth
      FROM trace.span
      WHERE run_id=(SELECT max(run_id) FROM trace.run) AND parent_span_id IS NULL
      UNION ALL
      SELECT s.span_id, s.process, s.name, s.dur_ms, s.t_start, t.depth+1
      FROM trace.span s JOIN t ON s.parent_span_id=t.span_id
      WHERE s.run_id=(SELECT max(run_id) FROM trace.run))
    SELECT lpad('', depth*2) || process || '.' || name AS span,
           round(dur_ms::numeric,1) AS dur_ms
    FROM t ORDER BY t_start;"

**Who waits for whom** (the cross-process wait edges; `overhead_ms` = wait −
SUM(children) = transport/queue, both monotonic-derived so skew-immune. `n_children`
is 1 by construction — each daemon wraps its handler in one root span — and `>1`
would flag a fan-out):

    psql -h 192.168.122.1 -d harness -c "
    SELECT waiter, wait_span, blocked_on, work_spans, n_children,
           round(waited_ms::numeric,1) AS waited_ms,
           round(work_ms::numeric,1)   AS work_ms,
           round(overhead_ms::numeric,1) AS overhead_ms
    FROM trace.blocking
    WHERE run_id=(SELECT max(run_id) FROM trace.run);"

**Aggregate, don't eyeball** — median/IQR per span (a perf claim cites this, never a
single `dur_ms`); record an overturnable interpretation in `trace.finding`:

    psql -h 192.168.122.1 -d harness -c "
    SELECT process, name, n, round(median_ms::numeric,1) AS median_ms,
           round((q3_ms-q1_ms)::numeric,1) AS iqr_ms, round(total_ms::numeric,1) AS total_ms
    FROM trace.span_stats WHERE run_id=(SELECT max(run_id) FROM trace.run);"

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
