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

`RemoteNLP` in `nlp_client.py` is a near-drop-in for a loaded `nlp`:
`.pipe(texts)` / `nlp(text)` return real `Doc` objects rehydrated from DocBin,
so guest-side extraction code is unchanged whether the model is local or remote.

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
