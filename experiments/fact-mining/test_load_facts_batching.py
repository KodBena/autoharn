"""test_load_facts_batching.py — the host-memory cap (--batch-size) must not change a
single DB row.

load_facts processes the corpus in batches of --batch-size, writing+freeing each batch
before fetching the next, so neither the daemon nor the client holds the whole book in
RAM. Correctness rests on one claim: every paragraph is an INDEPENDENT coref document, so
how requests are grouped is invisible to the output. This drives main() with a mocked
daemon + cursor at several batch sizes and asserts the execute() sequence is IDENTICAL —
including across a --max-sents budget cutoff (the running budget carries across batches)."""
import sys
from unittest import mock

import load_facts


def _facts(i):
    # one of each fact kind per paragraph, keyed by the paragraph index so the DB write
    # sequence is a deterministic function of paragraph order.
    return {
        "sents": [{"index": 0, "text": f"sent{i}"}],
        "entities": [{"sent": 0, "text": f"ent{i}", "canonical": f"ENT{i}", "label": "PERSON"}],
        "temporal": [{"sent": 0, "text": f"tmp{i}", "label": "DATE"}],
        "triples": [{"sent": 0, "subj": f"s{i}", "pred": "p", "obj": f"o{i}",
                     "subj_key": f"S{i}", "obj_key": f"O{i}", "negated": False}],
    }


class _Cur:
    def __init__(self, log):
        self.log = log
        self._id = 0

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        self._id += 1
        return (self._id,)            # monotone ids for doc_id / RETURNING sent_id

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Conn:
    def __init__(self, log):
        self.log = log

    def cursor(self):
        return _Cur(self.log)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeNLP:
    """A daemon stand-in: pipe_facts(batch) returns each paragraph's facts. The paragraph
    text is "P<i>", so the returned facts are a pure function of the batch contents — which
    is the whole point (grouping-invisible)."""
    last_coref_verify = None

    def __init__(self, *a, **k):
        pass

    def await_ready(self, *a, **k):
        return {"default": "test-model", "ok": True}

    def pipe_facts(self, batch):
        return [_facts(int(p[1:])) for p in batch]


def _run(tmp_path, n_paras, batch_size, max_sents=100_000):
    body = "\n\n".join(f"P{i}" for i in range(n_paras))
    path = tmp_path / "book.txt"
    path.write_text(body + "\n")

    log: list = []
    argv = ["load_facts.py", str(path), "--remote", "tcp://fake:1",
            "--coref", "--coref-backend", "jax-unified",
            "--body-start-line", "1", "--max-paras", str(n_paras),
            "--max-sents", str(max_sents), "--batch-size", str(batch_size),
            "--dsn", "postgresql://fake"]
    fake_mod = mock.MagicMock()
    fake_mod.RemoteNLP = _FakeNLP
    with mock.patch.object(sys, "argv", argv), \
         mock.patch.dict(sys.modules, {"nlp_client": fake_mod}), \
         mock.patch.object(load_facts.psycopg, "connect", return_value=_Conn(log)):
        assert load_facts.main() == 0
    return log


def test_batched_equals_one_shot_full(tmp_path):
    n = 10
    one_shot = _run(tmp_path, n, batch_size=10_000)   # 1 request
    batched3 = _run(tmp_path, n, batch_size=3)         # 4 batches
    batched1 = _run(tmp_path, n, batch_size=1)         # n batches

    assert one_shot == batched3 == batched1            # identical DB write sequence
    # non-vacuous: doc INSERT + per-paragraph (sentence + entity + temporal + assertion)
    assert len(one_shot) >= 1 + n * 4
    assert n > 1                                       # batching actually split


def test_batched_equals_one_shot_under_budget_cutoff(tmp_path):
    # one sentence per paragraph, budget cuts at 4 -> only the first 4 paragraphs written,
    # and the cutoff must land on the SAME paragraph regardless of batch boundaries.
    n, budget = 10, 4
    one_shot = _run(tmp_path, n, batch_size=10_000, max_sents=budget)
    for bs in (1, 2, 3, 7):
        assert _run(tmp_path, n, batch_size=bs, max_sents=budget) == one_shot
    # exactly `budget` sentence-inserts happened (not all n): 1 doc + budget*(4 facts)
    assert len([r for r in one_shot if "mining.sentence" in r[0]]) == budget
