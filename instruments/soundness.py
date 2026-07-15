#!/usr/bin/env python3
"""soundness — the derived-validity semantics of consult 11 §4.2, run over a real ledger.

The append-only ledger is two theories (consult 11 §4.1, FINDINGS F28): T_event (each row a
timestamped assertion — sound as history by construction) and T_now (what is CURRENTLY in force
— a NON-monotone closure over defeater edges, never stored). A consumer is UNSOUND exactly when
it reads T_event as if it were T_now. The deployed gate's enacts check is existence+precedence
only (it consults supersedes/status nowhere), so it derives tickets whose design antecedent has
been retired — the live gate_ok ∧ ¬sound_ok divergence this instrument computes.

Readouts (the §4.2 #show set, reproduced on live data):
  alias_surface(E,D)        — enacts edge whose target D is not a `decision` row.
  unsound_derivation(E,D)   — enacts edge the gate accepts (D earlier than E in id order) but
                              whose D is DEFEATED (a superseder of D precedes E in id order) —
                              sound_ok rejects it. Keyed on the integer id with strict `<`
                              (id-is-order, consult 17 §5.3; F-D retrofit 2026-07-06).
  launder(E,D,H)            — what auto-resolve-to-head would REWRITE the edge to (D's
                              supersession head H != D): a coherent-looking, FALSE record. This
                              is the proof (consult 11 §4.2) that auto-resolve launders the
                              alias; the only evidence-preserving enforcement is flag-and-journal.

Reads BOTH edge shapes (e9 scalar `enacts bigint`, e10 `enacts bigint[]`), auto-detected.
Acyclic by construction (append-only + FK-to-existing forces every edge strictly backward in
time), so the closure always terminates — no cycle handling needed (§4.2 acyclicity note).

Read-only. Consumes {session}.ledger. Nothing is written. The committed clingo program
`soundness.lp` is the same semantics as a parameterizable ASP artifact (§8.3).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

from ledger_target import LedgerTarget, resolve

# The target (db, schema, actor model) is resolved once per report() from the target NAME and
# every query goes through it — the SSOT that forecloses the wrong-place / missing-apparatus-
# object class (ledger_target.py; ADR-0000 Rule 2a). Module-global because report() sets it per
# invocation, mirroring the instrument's prior module-global connection constant.
TARGET: LedgerTarget


@dataclass(frozen=True)
class Row:
    id: int
    ts: str  # ISO string; string compare is chronological for this fixed format
    kind: str


def _rows(sql: str) -> list[list[str]]:
    return TARGET.rows(sql)


def _is_array() -> bool:
    return TARGET.scalar(
        f"SELECT data_type FROM information_schema.columns "
        f"WHERE table_schema='{TARGET.schema}' AND table_name='ledger' AND column_name='enacts';"
    ) == "ARRAY"


def _has_col(col: str) -> bool:
    """True iff the target's ledger carries `col` (the e13 amends/answers columns exist only on the
    s13+ / nla lineage; every readout that consumes them degrades to silence on the historical
    schemas — which are closed evidence, never migrated in place)."""
    return TARGET.has_col(col)


def load_amends(name: str) -> list[tuple[int, int, str]]:
    """The clause-level-defeat edges (A defeats clause `scope` of T). Empty on any pre-e13 schema.
    Consumer for the F44 aspectual gap: the vocabulary between whole-row supersede and silence.
    Self-contained: resolves and sets the shared TARGET, so an external caller (stale_enactment_debt)
    need not pre-set it."""
    global TARGET
    TARGET = resolve(name)
    if not _has_col("amends"):
        return []
    rel = TARGET.rel()
    return [(int(a), int(t), scope) for a, t, scope in
            _rows(f"SELECT id, amends, coalesce(amends_scope,'') FROM {rel} "
                  f"WHERE amends IS NOT NULL;")]


def load(name: str) -> tuple[dict[int, Row], list[tuple[int, int]], dict[int, int]]:
    """(rows by id, enacts edges (E,D), supersedes map child->parent). Resolves and sets TARGET."""
    global TARGET
    TARGET = resolve(name)
    rel = TARGET.rel()
    rows = {int(i): Row(int(i), ts.strip(), k.strip())
            for i, ts, k in _rows(f"SELECT id, to_char(ts,'YYYY-MM-DD HH24:MI:SS.US'), kind FROM {rel};")}
    if _is_array():
        edge_sql = (f"SELECT e.id, u.tid FROM {rel} e "
                    f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid);")
    else:
        edge_sql = f"SELECT e.id, e.enacts FROM {rel} e WHERE e.enacts IS NOT NULL;"
    edges = [(int(a), int(b)) for a, b in _rows(edge_sql)]
    sup = {int(a): int(b) for a, b in
           _rows(f"SELECT id, supersedes FROM {rel} WHERE supersedes IS NOT NULL;")}
    return rows, edges, sup


def _superseders(sup: dict[int, int]) -> dict[int, list[int]]:
    """parent D -> list of children X that supersede it (one hop). Transitive defeat needs only
    one superseding ancestor, so one-hop parents plus closure over them suffice."""
    inv: dict[int, list[int]] = {}
    for child, parent in sup.items():
        inv.setdefault(parent, []).append(child)
    return inv


# F-D ID-KEYING RETROFIT (clingo-fidelity review 2026-07-06; RATIFIED 2026-07-06, strict
# id-precedence -- deliberations/clause-defeat-decompose-then-overrule.md RATIFIED §2). This
# live-psql instrument formerly keyed defeat on TS with `<=` and head-resolution on newest-TS,
# while the ratified law and the id-keyed soundness.lp key on the integer ID with STRICT `<`
# (consult 17 §5.3 id-is-order). The two agree on every banked record (id-order == ts-order there,
# so banked outputs are UNCHANGED -- verified byte-identical, s10-s13/nla) but DIVERGED at the
# boundary: a self-superseding citation (a row that both supersedes D and enacts D) is called
# UNSOUND by ts-`<=` and SOUND by strict id-`<`. Retrofitted below to id-`<` / highest-id so this
# instrument conforms to the law and to its ASP twin. The operator-twin differential
# (soundness_twin.py, a close_manifest declared-observer line) is the standing net that makes a
# future keying divergence between soundness.py and soundness.lp a RED, non-skippable close line.
def _defeated_at(d: int, e: int, inv: dict[int, list[int]]) -> bool:
    """True iff some (transitive) superseder X of D precedes the citing row E in ID order (strict
    `<`) -- the id-keyed `defeated_asof(D,E) :- sup_star(X,D), X < E` of soundness.lp. id-is-order
    (consult 17 §5.3): id-order == ts-order on every banked record, but strict id-`<` correctly
    calls a self-superseding citation (X == E) SOUND where the former ts-`<=` called it unsound."""
    seen, stack = set(), list(inv.get(d, []))
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        if x < e:
            return True
        stack.extend(inv.get(x, []))
    return False


def _head(d: int, inv: dict[int, list[int]]) -> int:
    """The current head of a (possibly superseded) row: follow the INVERSE supersedes chain
    (a row X with supersedes=D is D's replacement), HIGHEST-ID branch at each step (id-is-order,
    consult 17 §5.3), to the row nothing supersedes. `supersedes(X,Y)` = X (newer, higher id)
    replaces Y (older), so the walk climbs from an old row to its live head. Retrofit of the former
    newest-ts branch selection; coincides on every banked record (id-order == ts-order)."""
    seen = set()
    while d in inv and d not in seen:
        seen.add(d)
        d = max(inv[d])
    return d


def derive(rows: dict[int, Row], edges: list[tuple[int, int]], sup: dict[int, int]
           ) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int, int]]]:
    """The PURE derived-validity core (§4.2), id-keyed (strict `<`; id-is-order, consult 17 §5.3):
    returns (alias_surface, unsound_derivation, launder) as edge tuples over the given
    rows/edges/supersedes. A pure function of typed inputs (ADR-0012 P9 functional core), so the
    operator-twin differential can run this EXACT keying over a boundary fixture without psql, and
    report() is a thin imperative shell over it. Semantics, matching soundness.lp:
      alias_surface(E,D) : enacts edge whose target D is not a `decision` row.
      unsound_derivation(E,D) : gate_ok(E) [enacts(E,D), D<E] but NOT sound_ok [some superseder of
                                D precedes E in id order] -- the deployed gate accepts, soundness
                                rejects.
      launder(E,D,H) : what auto-resolve-to-head would rewrite E's edge to (H = head(D) != D)."""
    inv = _superseders(sup)
    alias: list[tuple[int, int]] = []
    unsound: list[tuple[int, int]] = []
    launder: list[tuple[int, int, int]] = []
    for e, d in edges:
        if d in rows and rows[d].kind != "decision":
            alias.append((e, d))
        if e in rows and d in rows and d < e:        # gate_ok: id-precedence, strict
            if _defeated_at(d, e, inv):              # not sound_ok: superseder of D precedes E in id
                unsound.append((e, d))
                h = _head(d, inv)
                if h != d:
                    launder.append((e, d, h))
    return alias, unsound, launder


def report(name: str) -> None:
    rows, edges, sup = load(name)  # sets TARGET
    alias, unsound, launder = derive(rows, edges, sup)  # the pure id-keyed core (P9 shell)
    print(f"# soundness (derived-validity §4.2) — {TARGET.db}.{TARGET.rel()} "
          f"({len(rows)} rows, {len(edges)} enacts edges, {len(sup)} supersedes)\n")
    print("alias_surface(E,D)      — enacts target not a decision:")
    print("  " + (" ".join(f"alias_surface({e},{d})" for e, d in alias) or "(none)"))
    print("unsound_derivation(E,D) — gate_ok but antecedent defeated as of E.ts:")
    print("  " + (" ".join(f"unsound_derivation({e},{d})" for e, d in unsound) or "(none)"))
    print("launder(E,D,H)          — auto-resolve-to-head would rewrite E's edge to H (FALSE):")
    print("  " + (" ".join(f"launder({e},{d},{h})" for e, d, h in launder) or "(none)"))

    # ---- clause-level defeat (F44, e13 amends consumer) --------------------------------------
    # The aspectual gap made measurable: a HELD row whose specific clause is defeated by an in-force
    # amends edge, while the row survives whole-row supersession. This is exactly the s12 row-5-vs-29
    # negative the vocabulary could not previously express; soundness/stale-debt were structurally
    # blind to it (F44). An amends whose target is itself whole-row superseded is MOOT (the row is
    # gone); an amends whose author A is superseded is WITHDRAWN. Both are reported apart from the
    # live clause defeats so the readout does not over-warn.
    # ---- clause-level defeat (F44, e13 amends consumer) + condition-2 (MANDATORY) ---------------
    # The clause-defeat blocks below print only when there ARE amends edges (an empty domain has
    # nothing to enumerate). But the condition-2 detector's LINE is MANDATORY and prints
    # UNCONDITIONALLY (consult 19 §H / AC11): at zero amends it says so explicitly, so a reader can
    # never mistake "detector ran, found none" for "detector did not run" (ADR-0015 Rule 3/4, the
    # silent-non-run class this instrument was itself an instance of — link 21 F49). It ships WITH
    # the deferral, not after its first failure (ADR-0011 2026-07-02).
    amends = load_amends(name)
    inv = _superseders(sup)  # parent D -> superseders X (X replaces D); the clause-defeat block's
    #                          whole-row-gone test. (derive() computes its own inv internally; this
    #                          is the one the amends withdrawn/moot precedence below keys on.)
    live: list[tuple[int, int, str]] = []
    if amends:
        moot, withdrawn = [], []
        for a, t, scope in amends:
            t_gone = t in inv  # some row supersedes T (whole-row)
            a_gone = a in inv  # A itself superseded (the defeat withdrawn)
            if a_gone:
                withdrawn.append((a, t, scope))
            elif t_gone:
                moot.append((a, t, scope))
            else:
                live.append((a, t, scope))
        print("\nclause_defeat(A,T,scope) — in-force clause-level defeat (F44; target still whole-row in force):")
        print("  " + ("\n  ".join(f"clause_defeat({a},{t}): {scope}" for a, t, scope in live) or "(none)"))
        if moot:
            print("clause_defeat_moot(A,T)  — target was later whole-row superseded (amends subsumed):")
            print("  " + " ".join(f"moot({a},{t})" for a, t, _ in moot))
        if withdrawn:
            print("clause_defeat_withdrawn(A,T) — the defeating row A was itself superseded:")
            print("  " + " ".join(f"withdrawn({a},{t})" for a, t, _ in withdrawn))
    else:
        print("\nclause_defeat — the target carries no `amends` edges (no clause-level defeat domain).")
    # condition-2 standing detector — UNCONDITIONAL. Two or more IN-FORCE amends edges on ONE
    # target: the leading indicator that the row's INDIVIDUATION is wrong (accumulating clause-
    # defeats mean it is due decomposition, not a third patch — DTO re-entry condition 2, consult
    # 19 §1.7/§E). Fires on live clause-defeats only (moot/withdrawn do not accumulate).
    by_target: dict[int, list[int]] = {}
    for a, t, _ in live:
        by_target.setdefault(t, []).append(a)
    cond2 = {t: sorted(aa) for t, aa in by_target.items() if len(aa) >= 2}
    print("condition2_individuation(T) — >=2 in-force amends on one target (DTO re-entry cond. 2;"
          " the row is due decomposition, not a further amends):")
    if cond2:
        for t, aa in sorted(cond2.items()):
            print(f"  FIRED target #{t}: {len(aa)} in-force clause-defeats by rows {aa} "
                  f"-> escalate to the DTO build (consult 19 §1.7); do not add a third amends.")
    elif live:
        print("  (none — no target carries >=2 in-force amends)")
    else:
        print("  (none — 0 in-force amends edges, so no target can carry >=2; detector ran)")


if __name__ == "__main__":
    for s in (sys.argv[1:] or ["s11"]):
        report(s)
