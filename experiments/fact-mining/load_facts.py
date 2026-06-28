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

from extract import build_nlp, extract_triples, load_body, normalise

DSN = "host=192.168.122.1 dbname=harness"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--title", default="A Short History of Medicine")
    ap.add_argument("--model", default="en_core_web_sm")
    ap.add_argument("--remote", default=None)
    ap.add_argument("--cache", nargs="?", const="redis://127.0.0.1:6380/0", default=None)
    ap.add_argument("--body-start-line", type=int, default=834)
    ap.add_argument("--max-paras", type=int, default=200)
    ap.add_argument("--max-sents", type=int, default=400)
    ap.add_argument("--dsn", default=DSN)
    args = ap.parse_args()

    body = normalise(load_body(args.path, args.body_start_line))
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    nlp, model_label, cache = build_nlp(args.model, args.remote, args.cache, verbose=True)

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()][: args.max_paras]
    docs = nlp.pipe(paragraphs)

    n_assert = n_ent = n_temp = n_sent = 0
    with psycopg.connect(args.dsn) as conn, conn.cursor() as cur:
        # re-load = replace: drop any prior facts for this (text, model), cascade
        cur.execute("DELETE FROM mining.document WHERE sha256=%s AND model=%s", (sha, model_label))
        cur.execute(
            "INSERT INTO mining.document (path, title, sha256, model) "
            "VALUES (%s,%s,%s,%s) RETURNING doc_id",
            (args.path, args.title, sha, model_label),
        )
        doc_id = cur.fetchone()[0]

        for doc in docs:
            for sent in doc.sents:
                if n_sent >= args.max_sents:
                    break
                cur.execute(
                    "INSERT INTO mining.sentence (doc_id, sent_index, text) "
                    "VALUES (%s,%s,%s) RETURNING sent_id",
                    (doc_id, n_sent, sent.text.strip()),
                )
                sent_id = cur.fetchone()[0]
                span = sent.as_doc()

                for t in extract_triples(span):
                    cur.execute(
                        "INSERT INTO mining.assertion (sent_id, subj, pred, obj, negated) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (sent_id, t.subj, t.pred, t.obj, t.negated),
                    )
                    n_assert += 1
                for e in span.ents:
                    cur.execute(
                        "INSERT INTO mining.entity (sent_id, text, label) VALUES (%s,%s,%s)",
                        (sent_id, e.text, e.label_),
                    )
                    n_ent += 1
                    if e.label_ in ("DATE", "TIME"):
                        cur.execute(
                            "INSERT INTO mining.temporal (sent_id, text, label) VALUES (%s,%s,%s)",
                            (sent_id, e.text, e.label_),
                        )
                        n_temp += 1
                n_sent += 1
            if n_sent >= args.max_sents:
                break

    cstat = f" | cache {cache.stats()}" if cache else ""
    print(f"loaded doc_id={doc_id}: {n_sent} sentences, {n_assert} assertions, "
          f"{n_ent} entities, {n_temp} temporal{cstat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
