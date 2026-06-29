#!/usr/bin/env python
"""Mine facts from a text and load them into the `mining` schema (psql harness).

Reuses extract.py's parsing path (local / remote-GPU / cached, all the same) and
its SVO extraction, then writes the logic-agnostic base tables. The per-logic
views (classical / paraconsistent / temporal) are defined in schema.sql and need
no loader support — they are just SQL over what we insert here.

Apply the schema first:
    psql -h 192.168.122.1 -d harness -f schema.sql
Then load a sample:
    python load_facts.py /home/bork/pg/pg78966.txt --remote tcp://192.168.122.1:5599 --cache
"""

from __future__ import annotations

import argparse
import hashlib

import psycopg

# extract is now IMPORT-LIGHT (it lazy-imports spaCy only inside load_model), so these
# pure-text helpers + the SSOT extractor cost nothing on the remote path. The lard —
# `import spacy` -> thinc -> torch -> transformers — is never paid by `import load_facts`
# nor by the --remote codepath; the gate test_lean_remote_client.py forecloses its
# return. spaCy is pulled ONLY when a LOCAL model is actually loaded (build_nlp /
# load_model) or the local-coref pipeline is built (resolve.build_coref_nlp) — both
# strictly inside the non-remote branch below.
from extract import FactBundle, build_nlp, doc_to_facts, load_body, normalise
from spans import DEFAULT_DSN, get_tracer

# ONE home for "which harness DB" (ADR-0012 P1): the tracer's DEFAULT_DSN (itself
# HARNESS_DSN-overridable). The mining load and the trace store reach the same DB,
# so the DSN literal lives in exactly one place — spans.DEFAULT_DSN — not re-typed.
DSN = DEFAULT_DSN


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--title", default="A Short History of Medicine")
    ap.add_argument("--model", default="en_core_web_sm")
    ap.add_argument("--remote", default=None)
    ap.add_argument("--cache", nargs="?", const="redis://127.0.0.1:6380/0", default=None)
    ap.add_argument("--coref", action="store_true",
                    help="resolve pronouns with coref (entity normalization is "
                         "always applied either way). With --remote this uses the "
                         "daemon's maverick BATCHED encoder path by default (fast); "
                         "without --remote it uses the local fastcoref pipeline.")
    ap.add_argument("--coref-serial", action="store_true",
                    help="(remote coref only) force the SERIAL reference path on the "
                         "daemon instead of the batched encoder")
    ap.add_argument("--coref-verify", action="store_true",
                    help="(remote coref only) run BOTH serial and batched coref and "
                         "report a fidelity pass/fail. Run this ONCE before trusting "
                         "the batched path; the trusted serial clusters are loaded.")
    ap.add_argument("--coref-backend", default="maverick",
                    choices=["maverick", "jax-daemon"],
                    help="(remote coref only) decode backend on the daemon: 'maverick' "
                         "(reference, default — its own decode tail) or 'jax-daemon' "
                         "(retire the decode tail from the live path: the daemon's torch "
                         "encodes, the JAX decode daemon decodes).")
    ap.add_argument("--decode-addr", default=None,
                    help="(remote coref, jax-daemon backend) ZMQ address of the JAX "
                         "decode daemon (coref_decode_server.py). Passed through to the "
                         "spaCy daemon; defaults to its own --decode-addr if unset.")
    ap.add_argument("--body-start-line", type=int, default=834)
    ap.add_argument("--max-paras", type=int, default=200)
    ap.add_argument("--max-sents", type=int, default=400)
    ap.add_argument("--dsn", default=DSN)
    ap.add_argument("--trace", action="store_true",
                    help="mint a trace.run row and turn distributed-span tracing ON "
                         "across BOTH wires (client->nlp_server->decode daemon). Spans "
                         "land in the ephemeral `trace` schema (trace_schema.sql). "
                         "Off by default; orthogonal to the facts that get loaded.")
    args = ap.parse_args()

    # --trace mints the run_id (code-stamped) and enables tracing; the run context
    # then rides the ZMQ meta on each wire so the host daemons join this one trace.
    # Best-effort: a failed mint leaves tracing OFF and the load proceeds untraced.
    tracer = get_tracer()
    if args.trace:
        tracer.begin_run(process="client", dsn=args.dsn, config=vars(args))

    body = normalise(load_body(args.path, args.body_start_line))
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()

    # coref path/mode on the daemon: batched (fast, default), serial (reference),
    # or verify (run both, report fidelity). --coref-verify wins over --coref-serial.
    coref_mode = ("verify" if args.coref_verify
                  else "serial" if args.coref_serial else "batched")
    if (args.coref_serial or args.coref_verify) and not (args.coref and args.remote):
        print("note: --coref-serial / --coref-verify apply only to remote coref "
              "(--coref --remote ...); ignoring here.")

    cache = None
    remote_mode = bool(args.remote)
    if args.coref and args.remote:
        # coref on the host daemon; clusters are attached host-side and folded into the
        # JSON facts. backend = "maverick" (reference decode tail) or "jax-daemon" (torch
        # encodes on the daemon, the JAX decode daemon decodes — the decode tail retired).
        from nlp_client import RemoteNLP
        m = None if args.model == "en_core_web_sm" else args.model
        nlp = RemoteNLP(args.remote, model=m, coref=True, coref_mode=coref_mode,
                        coref_backend=args.coref_backend, decode_addr=args.decode_addr)
        model_label = f"{m or nlp.info().get('default', 'remote')}+coref({args.coref_backend}/{coref_mode})"
        print(f"=== remote coref daemon: {args.remote} | backend={args.coref_backend} | "
              f"mode={coref_mode} | {nlp.info()} ===")
    elif args.coref:
        # local fastcoref pipeline (guest-only; no remote/cache). resolve is lazy-imported
        # HERE — strictly inside the local branch — so the remote path never pulls it.
        import resolve
        nlp = resolve.build_coref_nlp(args.model)
        model_label = f"{args.model}+coref(fastcoref)"
        print(f"=== local coref pipeline: {args.model}+fastcoref ===")
    else:
        nlp, model_label, cache = build_nlp(args.model, args.remote, args.cache, verbose=True)

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()][: args.max_paras]

    # whole-run span: opened explicitly (not a `with`) so it wraps the pipe AND the
    # DB load below without reindenting the function; _NULL is a real nullcontext when
    # tracing is off, so __enter__/__exit__ are safe either way.
    run_span = tracer.span("client.run", n_paras=len(paragraphs), model=model_label)
    run_span.__enter__()

    # BOTH paths converge on `all_facts`: a list of per-paragraph fact dicts (the
    # extract.doc_to_facts shape). On --remote the DAEMON runs doc_to_facts and ships
    # JSON (lean client); locally we parse to Docs and run doc_to_facts here. ONE
    # extractor, two callers (ADR-0012 P1); ONE DB-load loop consumes the result below.
    all_facts: list[FactBundle]
    if remote_mode:
        all_facts = nlp.pipe_facts(paragraphs)
    else:
        all_facts = [doc_to_facts(doc) for doc in nlp.pipe(paragraphs)]

    # surface batched-vs-serial coref fidelity when --coref-verify was requested
    verify = getattr(nlp, "last_coref_verify", None)
    if verify is not None:
        status = "PASS" if verify.get("ok") else "FAIL"
        print(f"=== coref fidelity [{status}]: {verify.get('n')} paragraphs, "
              f"{verify.get('n_mismatch')} mismatch(es) — batched vs serial ===")
        for mm in verify.get("mismatches", []):
            print(f"  para {mm['index']}: serial={mm['serial']} batched={mm['batched']}")
        if status == "FAIL":
            print("  WARNING: batched coref diverged from serial. The trusted SERIAL "
                  "clusters were loaded; do NOT use --coref (batched) until resolved.")

    n_assert = n_ent = n_temp = n_sent = 0
    db_span = tracer.span("client.db_load")
    db_span.__enter__()
    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        # re-load = replace: drop any prior facts for this (text, model), cascade
        cur.execute("DELETE FROM mining.document WHERE sha256=%s AND model=%s", (sha, model_label))
        cur.execute(
            "INSERT INTO mining.document (path, title, sha256, model) "
            "VALUES (%s,%s,%s,%s) RETURNING doc_id",
            (args.path, args.title, sha, model_label),
        )
        doc_id = cur.fetchone()[0]

        # ONE DB-load loop over the SSOT fact dicts. doc_to_facts owns *what a fact is*;
        # this loop owns the running sentence budget and the DB identity — applying the
        # SAME budget the old inline loop did (a sentence past --max-sents is dropped,
        # and any entity/temporal/triple anchored to a dropped sentence is skipped via
        # `sent in sent_ids`). The extraction is identical pre/post (proven bit-for-bit
        # by test_doc_to_facts_equivalence.py); only its HOME moved.
        for facts in all_facts:
            # insert this paragraph's sentences; map doc-local index -> DB sent_id
            sent_ids: dict[int, int] = {}
            for s in facts["sents"]:
                if n_sent >= args.max_sents:
                    break
                cur.execute(
                    "INSERT INTO mining.sentence (doc_id, sent_index, text) "
                    "VALUES (%s,%s,%s) RETURNING sent_id",
                    (doc_id, n_sent, s["text"]),
                )
                sent_ids[s["index"]] = cur.fetchone()[0]
                n_sent += 1

            for e in facts["entities"]:
                if e["sent"] not in sent_ids:
                    continue  # sentence past the budget
                cur.execute(
                    "INSERT INTO mining.entity (sent_id, text, canonical, label) "
                    "VALUES (%s,%s,%s,%s)",
                    (sent_ids[e["sent"]], e["text"], e["canonical"], e["label"]),
                )
                n_ent += 1

            for tm in facts["temporal"]:
                if tm["sent"] not in sent_ids:
                    continue
                cur.execute(
                    "INSERT INTO mining.temporal (sent_id, text, label) VALUES (%s,%s,%s)",
                    (sent_ids[tm["sent"]], tm["text"], tm["label"]),
                )
                n_temp += 1

            for t in facts["triples"]:
                if t["sent"] not in sent_ids:
                    continue  # sentence past the budget
                cur.execute(
                    "INSERT INTO mining.assertion "
                    "(sent_id, subj, pred, obj, subj_key, obj_key, negated) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (sent_ids[t["sent"]], t["subj"], t["pred"], t["obj"],
                     t["subj_key"], t["obj_key"], t["negated"]),
                )
                n_assert += 1

            if n_sent >= args.max_sents:
                break
    db_span.__exit__(None, None, None)
    run_span.__exit__(None, None, None)
    # persist this process's buffered spans (best-effort; ADR-0002)
    written = tracer.flush()
    if args.trace:
        print(f"=== trace: run_id={tracer.run_id} | {written} client span(s) flushed "
              f"to the `trace` schema ===")

    cstat = f" | cache {cache.stats()}" if cache else ""
    print(f"loaded doc_id={doc_id} ({model_label}): {n_sent} sentences, {n_assert} assertions, "
          f"{n_ent} entities, {n_temp} temporal{cstat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
