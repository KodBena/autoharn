# `adjudicate` — usage

End-to-end, runnable guide to the package. For *why* it is shaped this way see
[DESIGN.md](DESIGN.md); for the coined terms see [GLOSSARY.md](GLOSSARY.md). This file
is the *how*.

## What it does

`adjudicate` is a reusable **human-OR-LLM interface for HITL adjudication**. One
[domain-schema](GLOSSARY.md#domain-schema) (a Python type artifact in `schema.py`)
drives everything: from it the package renders a prompt, a `less`-style preview pager,
and a table of unsupervised [classifications](GLOSSARY.md#classification), then collects
[adjudications](GLOSSARY.md#adjudication) (verdicts). The same schema derives the human
TUI, the headless/LLM driver, the wire codec, and the SQL DDL — there is no second
source of truth.

The live instance is **doc-selection**: "should this document go in the training
corpus?" over the RFC and UN-TEI corpora. A second instance, **coref-adjudication**
(BATCH), is defined for the parent project but not wired to a hook yet.

## Setup

```bash
cd experiments/adjudicate
. ~/w/vdc/venvs/generic/bin/activate      # textual + sqlalchemy live here; jax untouched
```

All commands below run from `experiments/adjudicate/` with that venv active. The modules
import flat (`python -m app`, `python -m read`), matching the test suite.

## The gates

```bash
MYPYPATH=. python -m mypy --config-file mypy.ini .    # type-driven: strict, no relaxations
python -m pytest tests/ -q                            # the suite
```

## Reading a document as plain text — the `read` command

The corpora are XML/structured; to read a UN-TEI document **as a normal text file**
(the XML stripped, paragraphs preserved), use `read`. It is the
[`DocumentSource`](docsource.py) functor instantiated for reading:
`UnTeiSource(...).map(render_paragraphs)` maps a readable-text content-transform over
the UN-TEI source, yielding a source whose documents *are* plain text (see
[the functor section](#the-documentsource-functor) below).

```bash
# read the first UN-TEI document (paged through less/$PAGER on a TTY):
python -m read --corpus un-tei

# list available document ids (id <TAB> UN symbol), capped:
python -m read --corpus un-tei --list --limit 20

# read a SPECIFIC document by id (the SAME id an adjudication task carries):
python -m read --corpus un-tei --doc tei:2000:td_x_:misc_6

# print plainly instead of paging (e.g. when piping):
python -m read --corpus un-tei --doc tei:2000:td_x_:misc_6 --no-pager

# same command as an app subcommand:
python -m app read --corpus un-tei --doc tei:2000:td_x_:misc_6
```

Sample output (XML fully stripped, multi-sentence paragraphs intact):

```
# tei:2000:td_x_:misc_6
# symbol: TD(X)/Misc. 6
# title:  The United Nations Parallel Corpus v1.0 - TD(X)/MISC.6
------------------------------------------------------------------------
...
In the 1950s, Raul Prebisch and the economists at the United Nations Economic
Commission for Latin America and the Caribbean (ECLAC) had developed a paradigm
that diverged from the neo-classical approach in several significant ways. They
had denounced the inequality in the relationship between the centre and the
periphery of the world economy, called for structural reforms and supported
import substitution strategies. ...
```

On a TTY the body is paged through the stdlib `pydoc.pager` (honors `$PAGER`/`less`);
piped or with `--no-pager` it prints plainly. The document id is `tei:` + the file's
path under the corpus root with `/`→`:` — identical to the id a doc-selection task
carries, so you can read exactly the document you are about to adjudicate.

### The `DocumentSource` functor

`docsource.py` defines `DocumentSource[T]`, a **functor** over a document's content
type: `map(f: A -> B)` lifts a content-transform to a structure-preserving source
transform — it changes *only* each document's content, never the document set, ids,
metadata, or order. It obeys the functor laws (identity / composition, asserted in
`tests/test_docsource_functor.py`). Reading is then just one content-transform
(`render_paragraphs`) mapped over `UnTeiSource`; a different way to read (a token
stream, a frequency table) is a different morphism over the *same* source — no second
parser. `loaders.UnTeiLoader` shares the same TEI parse (`parse_tei_paragraphs`), so
there is one TEI reader, not two.

## The adjudication flow (doc-selection)

`app.run` wires the four [seams](DESIGN.md#2-the-protocol-seams-adr-0012-p2--every-seam-a-protocol-1-real-adapter--the-second-designed-for)
from the one schema: a **loader** builds tasks from a corpus → the **Bus** carries them
→ a **Frontend** (human or headless) adjudicates → the **Store** persists.

```bash
# autonomous, NO LLM (RulePolicy: accept the model's suggested label), in-memory store:
python -m app --corpus rfc --limit 20 --frontend headless

# the human Textual TUI over UN-TEI (needs a TTY):
python -m app --corpus tei --limit 10 --frontend textual

# persist to a real SQLite file (durable across connections):
python -m app --corpus tei --limit 10 --frontend headless --db sqlite+pysqlite:///adj.db
```

`--corpus rfc` reads `/home/bork/distill/rfc/rfc*.txt`; `--corpus tei` reads
`/home/bork/distill/UNv1.0-TEI/**/*.xml`. `--limit` caps how many documents are loaded.

### The two frontends (one seam)

- **`textual`** — the human TUI ([`frontend_textual.py`](frontend_textual.py)): a prompt,
  a `VerticalScroll` preview pager (the document body), a `DataTable` of classifications,
  and verdict keys `1`/`2`/… (`1`=include, `2`=exclude); `q` quits. SINGLETON advances
  row-by-row.
- **`headless`** — the policy-driven surface ([`frontend_headless.py`](frontend_headless.py)),
  which **is** the LLM-driver mechanism, not a separate path. It serializes the *same*
  render-model to a transcript and asks a [policy](GLOSSARY.md#policy):
  - `RulePolicy` (the default `--frontend headless`) — deterministic, no LLM; accepts the
    unsupervised model's suggested label. Runs doc-selection end-to-end today.
  - `LLMPolicy` — hands the transcript to an injected `complete(prompt) -> str` seam (a
    real Claude call or a test fake) and parses the chosen verdict. Only the network call
    is deferred; the framing/parsing is real and tested.

Both are `protocols.Frontend`; `tests/test_frontend_parity.py` proves they return the
same adjudication contract for the same input.

### The store

`SqlStore` (SQLAlchemy Core) over one URL-parameterized adapter:

```bash
--db sqlite+pysqlite:///:memory:                       # default, ephemeral
--db sqlite+pysqlite:///adj.db                          # local file (durable)
--db postgresql+psycopg://USER@192.168.122.1/harness    # the prod psql harness
```

The table DDL is derived from `schema.store_columns()` — payload fields are stored as
`payload_<name>`, classification columns as `cls_<name>`, never hand-restated. `app.run`
prints how many records it persisted and a sample.

## Pointing at moved corpora

The corpus roots are `loaders.RFC_ROOT` and `docsource.TEI_ROOT` (re-exported as
`loaders.TEI_ROOT`). Construct a loader/source with an explicit `root=` to read from a
different path, e.g. `UnTeiLoader(root=Path("/other/UNv1.0-TEI"), limit=5)` or
`UnTeiSource(root=Path("/other/UNv1.0-TEI"))`.

## File map

See [DESIGN.md § File map](DESIGN.md#file-map). New since: `docsource.py` (the
`DocumentSource` functor + the UN-TEI source), `read.py` (the readable-paragraph
content-transform + the `read` CLI), `tests/test_docsource_functor.py`.
