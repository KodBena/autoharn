# Release provenance & licensing consult — `fact-mining`

> **Status:** informational provenance map for a prospective public release.
> **Scope of work:** inventory third-party provenance in this experiment and
> describe what licensing postures are actually feasible.

## 0. Scope and disclaimer (read first)

**This is NOT legal advice, and the author of this document is NOT a lawyer.**
It is an informational provenance/licensing map written by a technical consult
who read the code and the upstream license files. It records factual findings
(what is mirrored, what license each upstream actually ships) and reasons about
the *obligations those facts create*, but it cannot substitute for review by a
qualified IP attorney. **Before any public release, the two highest-stakes items
below (the maverick license + any redistributed model weights) should be
reviewed by a real lawyer.** Where a license could not be pinned down from the
artifacts on disk, the item is marked **MUST-VERIFY** rather than guessed.

All findings are dated **2026-06-29** against the code as it stood in the working
tree and the package versions installed in `~/w/vdc/venvs/generic`.

---

## 1. The headline finding (the one that drives everything)

**maverick-coref 1.0.7 is licensed `CC BY-NC-SA 4.0`** — Creative Commons
Attribution-**NonCommercial**-**ShareAlike** 4.0 International. Verified by
downloading the published sdist and reading its license file:

- `maverick-coref-1.0.7.tar.gz` → `LICENSE.txt`, first line:
  `Attribution-NonCommercial-ShareAlike 4.0 International`.
- Upstream: `https://github.com/sapienzanlp/maverick-coref`, author Giuliano
  Martinelli (SapienzaNLP). The sdist `PKG-INFO` says `License: UNKNOWN`
  (no SPDX field set), but the bundled `LICENSE.txt` is the unambiguous,
  full CC BY-NC-SA 4.0 legal text.

This matters because this repo does **two** things with maverick that are
governed by that license, not merely "use it as a library":

1. **It mirrors maverick's code line-for-line.** `jax_decode.py:14` —
   *"We mirror, line-for-line, maverick 1.0.7"* (then enumerates
   `maverick/models/model_mes.py`: `eos_mention_extraction`, `_calc_coref_logits`,
   `transpose_for_scores`, `mes_span_clustering`,
   `create_mention_to_antecedent_singletons`). The per-stage docstrings repeat
   this (`jax_decode.py:116,136,221`). `coref_host_shell.py` mirrors maverick's
   clustering/category/union-find/offset logic (`_get_categories_labels`,
   `create_clusters`, `original_token_offsets`). A line-for-line
   reimplementation of a copyrighted algorithm's *expression* is a **derivative
   work** of that code — translating Python→JAX is exactly the kind of
   "translated, altered, transformed" adaptation CC calls *Adapted Material*.
2. **It is built to load and (potentially) redistribute maverick's fine-tuned
   weights.** `export_deberta_maverick.py` exports maverick's fine-tuned DeBERTa
   encoder to `fixtures/deberta_maverick.npz`; `capture_fixtures.py:205` writes
   `fixtures/weights.npz` (the decode-tail learned parameters);
   `coref_decode_server.py:361` defaults `--weights ./fixtures/weights.npz`.
   These weight artifacts are *derived from maverick's CC BY-NC-SA checkpoint*
   and would carry the same license.

CC BY-NC-SA's operative constraints (from the bundled text):
- **NonCommercial** (Sec. 2(a)(1), Definition 1(k)): use "not primarily intended
  for or directed towards commercial advantage or monetary compensation."
- **ShareAlike** (Sec. 3(b)): any Adapted Material you Share must be licensed
  under CC BY-NC-SA (same elements) or a BY-NC-SA-compatible license.
- **Attribution** (Sec. 3(a)): retain creator identification, a copyright
  notice, a notice referring to the license + its disclaimer, a link to the
  material, and an indication that you modified it.

**Consequence:** the maverick-derived portions of this project **cannot** be
placed in the public domain or under a permissive license, and **cannot** be
ShareAlike-licensed in a way that also permits commercial use. This is the
single fact that most constrains the release. (Aside: Creative Commons itself
advises *against* using CC licenses for software; that doesn't make NC/SA
unenforceable here — it just means the upstream chose an awkward instrument, and
the obligations still bind.)

---

## 2. Provenance inventory

| Component | How it is used here | License (verified) | Obligation it creates |
|---|---|---|---|
| **maverick-coref 1.0.7** (SapienzaNLP) — decode-tail algorithm | **Code mirrored line-for-line** (`jax_decode.py:14`; `coref_host_shell.py` clustering/category/union-find) | **CC BY-NC-SA 4.0** (verified in sdist `LICENSE.txt`) | NonCommercial + ShareAlike + Attribution on the derivative. **Blocks PD/permissive on these files.** |
| **maverick-coref fine-tuned weights** (decode-tail `weights.npz`; fine-tuned DeBERTa `deberta_maverick.npz`) | **Weights derived & (potentially) redistributed** (`capture_fixtures.py:205`, `export_deberta_maverick.py:24`, `coref_decode_server.py:361`). *Not currently vendored in the repo* (see §4). | **CC BY-NC-SA 4.0** (inherited from the maverick checkpoint) — **MUST-VERIFY** the model-card/HF-repo terms specifically | Same NC+SA+Attribution. Redistributing the weights publishes a CC BY-NC-SA artifact. Highest-stakes item. |
| **HuggingFace `transformers` 4.53.2** — DebertaV2 modeling code | **Code mirrored line-for-line** (`jax_deberta.py:13` mirrors `transformers/models/deberta_v2/modeling_deberta_v2.py`) | **Apache-2.0** (verified: `transformers-4.53.2.dist-info/LICENSE`, metadata `License: Apache 2.0`) | Apache-2.0 §4: retain copyright/notice/attribution; if a `NOTICE` exists, propagate it; state significant changes. Permissive — compatible with release, but **requires attribution + NOTICE**. |
| **`microsoft/deberta-v3-large`** — architecture mirrored by `jax_deberta.py`; base weights maverick fine-tuned | Architecture **reimplemented**; base weights are upstream of the fine-tune | **MIT** for the model (per HF model card) — **MUST-VERIFY** model card at release time (code-license vs weights-license can differ) | MIT: keep copyright + permission notice. Permissive. The *base* weights are MIT, but the *fine-tuned* weights are governed by maverick's NC/SA (more restrictive license wins on the derivative). |
| **`spaCy` 3.8.14 + `en_core_web_trf` 3.8.0 / `en_core_web_sm`** | **Library import** (runtime dependency, not redistributed) | **MIT** (verified: `pip show`) | Attribution if redistributed. As a dependency (pip-installed, not vendored), only standard attribution. Note model **training-data provenance** (OntoNotes 5 etc.) is documented in the model card but does not bind a *user* of the MIT-licensed model. |
| **`fastcoref` 2.1.6** | **Library import** (referenced/used as a coref option) | **MIT** (verified: `pip show`) | Attribution if redistributed; otherwise standard dependency. |
| **`jax` / `jaxlib` 0.10.1** | Library import (the device core) | **Apache-2.0** (verified) | Attribution/NOTICE if redistributed; dependency only here. |
| **`numpy` 2.4.6** | Library import | **BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0** (verified `License-Expression`) | Permissive; attribution if redistributed. Dependency only. |
| **`torch` 2.12.1** | Library import (host-only encoder + checkpoint load) | **BSD-3-Clause** (verified) | Permissive; dependency only. |
| **`pyzmq` 27.1.0** | Library import (wire transport) | **BSD-3-Clause** (verified) | Permissive; dependency only. |
| **`psycopg` 3.3.4** | Library import (fact store) | **LGPL-3.0-only** (verified `License-Expression`) | LGPL: fine to *use* as an unmodified library dependency; obligations trigger mainly if you **modify and redistribute psycopg itself** (not the case here). Worth a one-line note; not a blocker. |
| **`spacy-transformers` 1.4.0** | Library import | **MIT** (verified) | Attribution if redistributed; dependency only. |
| **Project Gutenberg text `pg78966.txt`** (Singer, *A Short History of Medicine*, 1928) | **Data / PoC input** (`README.md`, `extract.py`) | Underlying work **public domain in the US**; the PG *edition* carries PG's **trademark + license terms** (verified header + §1 of the embedded PG License) | The book's *text* is free to reuse. But if you redistribute the **PG edition** while keeping PG references, PG's terms attach (esp. the "Project Gutenberg" **registered trademark** restriction, §1.B; and the full-license/attribution requirements, §1.E). See §4. |
| **chocofarm ADRs** (the project's own governance docs the code cites) | Methodology the maintainer authored | Maintainer's own (Unlicense / public-domain per their footers) | None on third parties — these are the maintainer's to dedicate. |

---

## 3. The central tension: why a blanket Public-Domain / Unlicense is not clean here

The maintainer's default posture is **Public Domain / the Unlicense**, grounded
in a personal ethical view: *"with AI, everything produced by AI belongs to
everyone, because of how AI are trained."*

That is a coherent **ethical** position, and it can absolutely govern the
maintainer's *own* contributions. But it has no purchase on the *legal* status
of third-party material, for a simple reason: **copyright law does not condition
an upstream license on how a model was trained.** maverick's CC BY-NC-SA grant,
transformers' Apache-2.0 grant, etc., bind a redistributor regardless of the
redistributor's philosophy about AI and training data. A public-domain
*dedication* (CC0/Unlicense) is an act you can only perform over rights **you
hold** — you cannot dedicate to the public a work whose copyright belongs to
someone else, and you cannot strip an upstream's conditions off a derivative of
their work by re-labeling it.

So the release has to be split into three legally distinct buckets:

- **(a) The maintainer's genuinely original code.** Everything that is *not* a
  mirror of an upstream — the ZMQ wire protocol and servers/clients
  (`nlp_server.py`, `nlp_client.py`, `coref_decode_server.py`,
  `coref_decode_client.py`), the fact-store schema and loaders
  (`schema.sql`, `load_facts.py`, `extract.py`, `resolve.py`, `spans.py`),
  the caching layer (`nlp_cache.py`), the import-XOR / device-transfer gates and
  their tests, the safe-load policy (`maverick_load.py`), the boundary/fixture
  scripts as *original orchestration*. **This is the maintainer's to dedicate to
  the public domain or license however they like.** The AI-philosophy lives
  here, legitimately.
- **(b) Mirrored / derivative code governed by upstream.**
  - `jax_deberta.py` — derivative of transformers' DebertaV2 (**Apache-2.0**).
    Apache is permissive, so this can ship — *but* it carries Apache-2.0's
    attribution + NOTICE-propagation + state-changes obligations. It is **not**
    public-domain-able; it must remain Apache-2.0-attributed (you may dual-state
    it, but you cannot erase the upstream notice).
  - `deberta_weights.py`, `export_deberta_maverick.py` — conversion code that
    mirrors HF resolution logic; Apache-2.0 lineage; same treatment.
  - `jax_decode.py`, `coref_host_shell.py` — derivative of **maverick
    (CC BY-NC-SA 4.0)**. These are the hard ones: **NonCommercial + ShareAlike**.
    They cannot be PD, cannot be MIT/Apache, and their ShareAlike pulls toward
    CC BY-NC-SA for the combined adapted work.
- **(c) Redistributed model weights governed by the model license.** If the repo
  ever ships `fixtures/weights.npz` or `fixtures/deberta_maverick.npz`, those are
  CC BY-NC-SA artifacts (maverick fine-tune). This is usually the *real*
  operative constraint, because weights are the thing most likely to be treated
  as the protected deliverable.

The blunt summary: **a single repo-wide `LICENSE: Unlicense` would be
inaccurate and would misrepresent (b) and (c) to downstream users.** The honest
move is a per-bucket posture (see §5).

---

## 4. The two sharpest items

### (i) maverick — mirrored decode logic + (prospective) redistributed weights

- **License: CC BY-NC-SA 4.0 — CONFIRMED** (not a guess; read from the sdist).
  This is *restrictive in two independent ways the project cares about*:
  NonCommercial (so the project can't be offered for commercial advantage while
  carrying these parts) and ShareAlike (so the adapted parts must stay
  CC BY-NC-SA — directly incompatible with a PD/Unlicense dedication and with a
  plain permissive license).
- **Mirrored code** (`jax_decode.py`, `coref_host_shell.py`): being a
  transformation of maverick's expression, it is Adapted Material. To ship it
  you must (a) attribute SapienzaNLP/Martinelli + link the source + note your
  modifications, and (b) license *that adapted material* CC BY-NC-SA 4.0. You
  cannot relicense it permissively or dedicate it to the PD.
- **Weights** (`fixtures/weights.npz`, `fixtures/deberta_maverick.npz`):
  **GOOD NEWS — these are NOT currently vendored in the working tree.** There is
  no `fixtures/` directory in the repo; the code *references* these paths and the
  export/capture scripts *produce* them on the host, but the artifacts are not
  committed. The current de-facto posture is therefore already the safe one.
  - **MUST-VERIFY:** confirm the exact terms attached to maverick's published
    checkpoint on its HF model repo (the *checkpoint* may carry the same
    CC BY-NC-SA, or an additional model-card clause). Treat as CC BY-NC-SA until
    proven otherwise.
  - **Recommendation: do NOT vendor the weights.** Keep load-at-runtime + a
    documented "how to obtain maverick's checkpoint from its official source."
    This avoids the maintainer becoming a redistributor of a CC BY-NC-SA model
    artifact, which is the single highest-liability act available in this repo.

### (ii) The DeBERTa weights' model license

- **`microsoft/deberta-v3-large` is MIT for the model** (per the HF model card)
  — **MUST-VERIFY** at release (Microsoft sometimes separates a code license
  from a model/weights license; confirm the model card's `license:` field the
  day you release).
- The crucial subtlety: even though the **base** DeBERTa weights are MIT, the
  weights this project actually uses are maverick's **fine-tune** of them. The
  fine-tuned weights are a derivative under maverick's CC BY-NC-SA — **the more
  restrictive upstream governs the derivative.** So "DeBERTa is MIT" does not buy
  you a permissive path for the encoder weights as used here; it only matters if
  you were to ship *vanilla* deberta-v3-large weights (which the fidelity tests
  use as a stand-in, per `export_deberta_maverick.py:36-39`).
- Same recommendation: prefer load-at-runtime from HF over vendoring; if you do
  vendor vanilla deberta-v3-large for the round-trip test fixtures, that's MIT
  and fine *with* the MIT notice — but keep it clearly separated from the
  maverick fine-tune.

---

## 5. Recommended posture(s), ranked

**Posture A (recommended): per-bucket licensing + a provenance/notice file.**

1. **The maintainer's original code (bucket a):** license as the maintainer
   prefers. Their PD/Unlicense or CC0 instinct is *fully legitimate here*. (If
   they want maximum downstream usability and the option of others combining it
   with permissive code, **MIT or Apache-2.0** is friendlier than the Unlicense —
   the Unlicense has known patent-grant and acceptance ambiguities — but PD/CC0
   is defensible. This is where the AI-philosophy can be stated, as the
   maintainer's own dedication.)
2. **transformers-derived code (`jax_deberta.py`, `deberta_weights.py`,
   `export_deberta_maverick.py`):** keep **Apache-2.0**, with an SPDX header and
   a pointer to the upstream file mirrored. Propagate any upstream `NOTICE`.
3. **maverick-derived code (`jax_decode.py`, `coref_host_shell.py`):** mark
   **CC BY-NC-SA 4.0**, attribute SapienzaNLP/Martinelli, link the source, note
   "modified: reimplemented in JAX." Accept that these files are NonCommercial +
   ShareAlike.
4. **Weights:** don't vendor; document how to obtain them; note their
   CC BY-NC-SA status.
5. **Add a top-level `THIRD-PARTY-NOTICES.md` / `PROVENANCE.md`** (this document
   is most of its substance) and a `NOTICE` file capturing the Apache-2.0 +
   CC BY-NC-SA + MIT attributions.

Net effect: because buckets (b)/(c) include a NonCommercial + ShareAlike
component, **the repository *as a whole* is effectively NonCommercial** for any
distribution that includes the maverick-derived files. That is unavoidable while
those files are present — it's a property of the upstream choice, not of the
maintainer's posture.

**Posture B (cleanest legally, more work): isolate or remove the NC/SA parts.**

If the maintainer wants a genuinely permissive / PD-able release, physically
**separate** the maverick-derived decode tail into its own clearly-CC-BY-NC-SA
subdirectory (or a separate optional repo), so the *core* project can be
permissive and the NC/SA coref-decode is an opt-in plugin the user installs
themselves. Best long-term option *if* the project ever wants commercial-friendly
adoption — but it's real refactoring.

**Posture C (NOT recommended): single repo-wide Unlicense/PD.** Inaccurate;
misrepresents the Apache, MIT and (especially) CC BY-NC-SA obligations to
downstream users; the kind of thing that's harmless until it isn't.

---

## 6. "Before public release" checklist

- [ ] **Verify maverick's license at the source** — confirm CC BY-NC-SA 4.0 on
      both the `sapienzanlp/maverick-coref` repo *and* the published model
      checkpoint/model card (code vs weights may differ). *(Currently confirmed
      CC BY-NC-SA from sdist `LICENSE.txt`; re-confirm the checkpoint terms.)*
- [ ] **Resolve the weights** — decide explicitly: do **not** vendor
      `fixtures/weights.npz` / `fixtures/deberta_maverick.npz`; ship a
      "how to obtain" doc + a runtime loader. Confirm `.gitignore` keeps
      `fixtures/` out of the published tree. *(Already absent today — keep it so.)*
- [ ] **Verify the DeBERTa model card** `license:` field for
      `microsoft/deberta-v3-large` (expected MIT) the day of release.
- [ ] **Add per-file SPDX headers + upstream attribution** to every mirrored
      file: `jax_decode.py` and `coref_host_shell.py` → CC BY-NC-SA 4.0 +
      "derived from maverick 1.0.7 `model_mes.py`, © SapienzaNLP"; `jax_deberta.py`,
      `deberta_weights.py`, `export_deberta_maverick.py` → Apache-2.0 + "derived
      from HuggingFace transformers `modeling_deberta_v2.py`."
- [ ] **Add a `NOTICE` + `THIRD-PARTY-NOTICES.md`** (Apache-2.0 §4 attribution,
      CC BY-NC-SA attribution, MIT/BSD notices for the dependency stack).
- [ ] **Confirm Gutenberg edition terms** — if `pg78966.txt` is shipped as
      sample data, either (a) strip all "Project Gutenberg" references and ship
      only the public-domain *text* (PG §1.E lets you remove references and reuse
      the underlying PD work without PG's terms/trademark), or (b) keep the PG
      edition *with* its full embedded license and respect the registered
      trademark (PG §1.B). Cleanest: keep only a small excerpt or ship a
      downloader, not the full PG file with its boilerplate stripped halfway.
- [ ] **psycopg (LGPL):** add a one-line note that it's an unmodified LGPL
      dependency (use is fine; you are not modifying/redistributing psycopg).
- [ ] **Decide the original-code license** (PD/Unlicense vs MIT/Apache) and state
      the AI-philosophy explicitly as *the maintainer's dedication of their own
      contributions* — not as a claim over upstream parts.
- [ ] **Real-lawyer review** of items (i) and (ii) before any release that could
      be read as commercial or that vendors weights.

---

## 7. Proportionality note

The maintainer correctly observes that their projects attract little public
scrutiny, and the *practical* enforcement risk of a low-traffic experimental
research repo is genuinely low — most CC BY-NC-SA / Apache obligations are
honored informally and rarely litigated against hobby-scale academic
reimplementations. That's a fair read of the *risk*, and this document is not
trying to inflate it.

But two honest caveats:

1. **Low scrutiny ≠ no obligation.** The obligations exist the moment you
   distribute; "nobody looked" is a statement about probability of consequence,
   not about compliance. The cheap insurance — per-file attribution + a NOTICE +
   not vendoring weights — costs an afternoon and removes essentially all of the
   *avoidable* exposure.
2. **The weights and the maverick mirror are the items that would actually
   matter if the project ever gained traction** — e.g. if it were cited, forked
   into something commercial, or picked up by people who *do* read licenses.
   SapienzaNLP is an active academic group that deliberately chose a
   NonCommercial license; that is exactly the kind of upstream that notices
   commercial reuse of its model. So: keep the dependency stack relaxed (it's
   nearly all MIT/BSD/Apache and unproblematic), and spend the care budget on the
   two sharp items.

**Bottom line:** ship the maintainer's own code however they ethically prefer;
honor Apache/MIT with notices (cheap, permissive); treat maverick's CC BY-NC-SA
mirror + weights as the real constraint — attribute them, keep them
NonCommercial/ShareAlike, and do not vendor the weights. That combination is both
faithful to the upstreams and maximally faithful to the maintainer's
public-everything instinct *over the parts that are actually theirs to give*.
