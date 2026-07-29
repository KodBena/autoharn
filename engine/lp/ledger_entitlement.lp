% ===========================================================================
% ledger_entitlement.lp -- the s60 entitlement-enforcement ASP twin (design/
% FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 item 2: "the ASP twin ships in the SAME delta... not
% filed as pairing debt"). Derives reaches_genesis/1, the independent SECOND derivation of
% kernel/lineage/s60-entitlement-enforcement.sql's SQL function
% principal_authority_chain_reaches_genesis(pid) -- ./judge holds the SQL/ASP differential in
% AGREE on this delta's fixture (seen-red/s60-entitlement-enforcement/).
%
% s62 EXTENSION (kernel/lineage/s62-delegation-lifecycle-gating.sql, design/
% FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 AMENDMENT, row 1385): s62 adds a SEVENTH SQL-side
% authority-bearing act class (delegation_lifecycle -- principal_relation_asserted/'acts-for'
% rows themselves now require the WRITER's chain to reach genesis) but requires NO new predicate
% here. reaches_genesis/1 was never act-class-specific -- it is the chain closure over
% acts_for_edge/2 for ANY principal, consulted identically regardless of which act class asked
% "does this actor's chain reach genesis". s62's SQL side calls the SAME
% principal_authority_chain_reaches_genesis(pid) this program already twins; no new EDB family,
% no new rule. ./judge continues to hold AGREE on seen-red/s62-delegation-lifecycle-gating/'s own
% fixture, including the attack scenario itself (a chainless principal's self-asserted acts-for
% edge is refused before it is ever written, so it never enters either side's EDB -- AGREE here
% is a statement about the chain the exporter reads, unaffected by which candidate writes the
% SQL trigger refused before they became rows).
%
% LOAD ORDER: loaded ON TOP OF ledger_tnow.lp -- the chain closure below is stratified BESIDE
% in_force/1, never into it (spec §1 item 2, verbatim: "the chain closure in the ledger_defeat.lp
% stratification shape, beside in_force/1, never into it" -- the SAME stratification discipline
% ledger_defeat.lp's own header states as its three binding laws, applied here to a second
% closure over a DIFFERENT EDB family (acts-for delegation, not defeat)). engine/lp_registry.py's
% "entitlement" LAYER is the checkable required stack (ledger_tnow.lp, ledger_entitlement.lp).
%
% THE SAME STRATIFICATION LAW THIS FILE OBEYS (ledger_defeat.lp's own law 1, applied one layer
% over): every hop test is `principal_active/1` over a PRESENT-TENSE fact (never `not
% principal_suspended_row/1` re-derived here -- the exporter emits principal_active/1 already
% filtered by kernel.principal_standing, the SQL twin's own source of truth) -- entitlement never
% recomputes standing, it CONSUMES the one already-derived fact, matching how ledger_defeat.lp
% consumes superseded/1 rather than re-deriving supersession.
%
% EDB (engine/ledger_edb.py's export_entitlement(); a fact family absent because the target
% cannot produce it is a DECLARED EXCLUSION in the capability manifest, never silence -- I12):
%   principal(P).          P is a registered principal (any standing) -- the domain the genesis
%                         exception below quantifies over (the SQL twin's own function takes ONE
%                         pid at a time; this program compares the FULL reaches_genesis SET
%                         against the SQL side evaluated once per registered principal, so the
%                         exception needs its own domain fact here).
%   acts_for_edge(X,Y).   X's in-force principal_relation_asserted 'acts-for' row names Y as the
%                         far endpoint (X acts-for Y -- X's authority derives from Y).
%   genesis(G).           G is the world's genesis principal (entitlement_genesis_principal(),
%                         the SQL twin's own source -- emitted as AT MOST one fact; absent when
%                         no principal has ever been registered, matching the SQL function's own
%                         NULL case).
%   principal_active(P).  P's CURRENT standing (kernel.principal_standing) is 'active' -- the
%                         fact a chain hop's delegating principal must satisfy (I5: a suspended/
%                         revoked delegate severs every chain through them PROSPECTIVELY; this
%                         program is evaluated fresh per fixture snapshot, never cached, matching
%                         the SQL twin's own "computed at read" law).
% ---------------------------------------------------------------------------

% Declared-optional EDB families (empty extension = silence, the house #defined idiom):
#defined principal/1.
#defined acts_for_edge/2.
#defined genesis/1.
#defined principal_active/1.
% Consumed from ledger_tnow.lp when stacked (LAYERS "entitlement") -- soft, unread by name here;
% this program does not itself gate on in_force/1/superseded/1 (acts_for_edge/2 is ALREADY the
% in-force reading, s41 D-5's principal_relations view -- the exporter's own job, mirroring how
% ledger_defeat.lp's trust_grant/3 arrives pre-filtered rather than re-derived from raw facts).
#defined in_force/1.
#defined superseded/1.

% THE GENESIS EXCEPTION (kernel/lineage/s60-entitlement-enforcement.sql Element 6, mirrored
% exactly): when NO genesis fact is exported at all (no principal has ever been registered),
% every registered principal trivially reaches genesis -- the SQL twin's own bootstrapping edge,
% re-derived here rather than asserted, so a fixture exercising the empty-world case stays
% comparable. Quantifies over principal/1 (never acts_for_edge/2), so a lone principal with no
% delegation facts at all still reaches genesis under this exception, matching the SQL function
% called on ANY pid when entitlement_genesis_principal() IS NULL.
reaches_genesis(X) :- principal(X), not genesis(_).

% THE CHAIN RULE (envelope shape, mirroring ledger_defeat.lp's model_defeated/3 stratification):
% X reaches genesis if X IS genesis, or X acts-for some Y that is itself active and reaches
% genesis. The base case and the recursive step are two separate rules, exactly ledger_defeat's
% own "beside, never into" idiom for a second stratum (here: a second base case beside the
% recursive one, not folded into a single disjunctive rule).
reaches_genesis(X) :- genesis(X).
reaches_genesis(X) :-
    acts_for_edge(X,Y),
    principal_active(Y),
    reaches_genesis(Y).

#show reaches_genesis/1.

% ===========================================================================
% s64 EXTENSION (kernel/lineage/s64-principal-stamps-delegation-conditions.sql, design/
% FABLE-PRINCIPAL-STAMPS-SPEC.md §3 item 4: "the ASP twin gains the SAME conjunction in its
% stratified closure, beside in_force/1, never into it"). reaches_genesis_scoped/2 is a SECOND,
% ADDITIONAL predicate -- BESIDE reaches_genesis/1 above, never folded into it, matching this
% file's own s62-extension precedent one layer up: reaches_genesis/1's own rules are UNTOUCHED
% (byte-identical), so ./judge's existing AGREE leg on reaches_genesis/1 is unaffected by this
% addition. Independently re-derives kernel/lineage/s64-...sql's SQL 2-arg
% principal_authority_chain_reaches_genesis(pid, act_class) -- "refuses any act outside the
% intersection of every edge's grant and conditions along the path" (spec §2.2): conjunction
% along a recursive walk IS an intersection, by construction.
%
% NO ASP TWIN for the depth-budget (no-redelegate) or must-countersign conjuncts -- named,
% deferred LIMITS (s64's own header, and this build's report): both are single-hop-or-aggregate
% checks over already-in-force facts, the SAME shape s61 itself precedent-deferred ("an ASP twin
% for a single-hop existence check would mirror the SQL query nearly verbatim"). Proven only by
% the RED/GREEN fixture legs, never by this differential.
%
% EDB (engine/ledger_edb.py's export_entitlement(), s64 addition -- purely additive, the four
% families above are UNCHANGED):
%   act_class(C).            The kernel-computed act-class vocabulary (eight tokens as of s64) --
%                             a fixed, named domain (this project's own STANDARDS-REGISTRY
%                             posture: named, never corpus-discovered).
%   delegation_edge(X,Y).    THE SCOPED CLOSURE'S OWN EDGE RELATION -- a SUPERSET of
%                             acts_for_edge/2 (which stays 'acts-for'-only, byte-identical, so the
%                             s60/s62 reaches_genesis/1 differential above is UNTOUCHED): X's
%                             in-force principal_relation_asserted row naming Y as object,
%                             relation acts-for OR dispatched-by (the hazard-in-reach fix, kernel/
%                             lineage/s64-...sql's own header), UNEXPIRED (the exporter's own
%                             pre-filter -- expiry is CONSUMED here, never re-derived in ASP,
%                             mirroring how principal_active/1 is already a pre-filtered fact,
%                             this file's own header law, applied to expiry identically).
%   edge_scope_class(X,Y,C). Edge (X,Y) (a delegation_edge/2 member) is scoped to permit act
%                             class C -- one fact per (edge, permitted class).
%   edge_unscoped(X,Y).      Edge (X,Y) carries NO scope restriction (backs every act class) --
%                             mutually exclusive with edge_scope_class for the SAME (X,Y).
% ---------------------------------------------------------------------------
#defined act_class/1.
#defined delegation_edge/2.
#defined edge_scope_class/3.
#defined edge_unscoped/2.

edge_permits(X,Y,C) :- delegation_edge(X,Y), act_class(C), edge_unscoped(X,Y).
edge_permits(X,Y,C) :- edge_scope_class(X,Y,C).

reaches_genesis_scoped(X,C) :- principal(X), act_class(C), not genesis(_).
reaches_genesis_scoped(X,C) :- genesis(X), act_class(C).
reaches_genesis_scoped(X,C) :-
    delegation_edge(X,Y),
    principal_active(Y),
    edge_permits(X,Y,C),
    reaches_genesis_scoped(Y,C).

#show reaches_genesis_scoped/2.

% ===========================================================================
% s70 EXTENSION (kernel/lineage/s70-scope-binding.sql, design/FABLE-ACCESS-CONTROL-AND-
% INFORMATION-FLOW-SPEC.md §1b/§1c, design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1c):
% the scope-visibility predicates, BESIDE reaches_genesis/reaches_genesis_scoped above, never
% folded into them -- this file's own precedent, one layer over (the s62/s64 extensions above
% each added rules beside the prior stratum, never edited it; reaches_genesis/1 and
% reaches_genesis_scoped/2's own rules are UNTOUCHED, byte-identical, by this addition).
%
% EDB (engine/ledger_edb.py's export_entitlement(), s70 addition -- purely additive, every family
% above is UNCHANGED):
%   scope_binding_row(P).   P holds a CURRENT in-force principal_scope_bound row (principal_scopes'
%                           own row existence, supersession-aware) -- ROW EXISTENCE, not surface
%                           count, is what arms a scope (see scope_armed/1 below): a binding with
%                           NULL/empty scope_surfaces still arms, fail-closed.
%   scope_bound(P,S).       One fact per element of P's bound scope_surfaces array.
%   scope_disclosure(P,M).  P's bound scope_disclosure_mode, when declared (NULL emits no fact on
%                           either producer -- absence of a declared tier is absence).
%   surface(S).             The closed route/view vocabulary, injected from the SAME single home
%                           (serving/boundary_service.py's VIEW_REGISTRY) both producers read.
% (scope_exclusion/3 is ALSO exported but has no #show/derivation here -- the deferred row-level
% exclusion derivation, see this file's own header LIMITS note below.)
% ---------------------------------------------------------------------------
#defined scope_binding_row/1.
#defined scope_bound/2.
#defined scope_disclosure/2.
#defined surface/1.
#defined scope_exclusion/3.

% scope_armed(P): FAIL-CLOSED arming -- a principal with an in-force binding is scoped even when
% the binding's scope_surfaces is NULL/empty (a representable s70 state: binding row present, zero
% surfaces, exclusions present). Such a binding grants nothing rather than everything -- the
% serving filter MUST key on this SAME row-existence predicate (spec §1c).
scope_armed(P) :- scope_binding_row(P).

% open_scope(P): the fail-safe default as a rule -- on any world with zero scope facts (including
% every pre-s70 world, and every s70-capable-but-unarmed principal), every principal derives
% open_scope. Byte-identical-unarmed-world guarantee, a one-line consequence of negation-as-
% failure over scope_armed/1 (never re-testing scope_binding_row/1 directly here).
open_scope(P) :- principal(P), not scope_armed(P).

% may_read_surface(P,S): named at its honest granularity -- SURFACE visibility only. Row-level
% exclusion behavior is deliberately NOT derived this increment (see this file's own header
% LIMITS note); the name says so.
may_read_surface(P,S) :- open_scope(P), surface(S).
may_read_surface(P,S) :- scope_bound(P,S).

#show open_scope/1.
#show may_read_surface/2.
#show scope_disclosure/2.

% DEFERRED DERIVATION, NAMED (design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1c/§3): NO
% ASP twin for row-level exclusion denial. scope_exclusion/3 facts are exported from day one, but
% no derived per-row denial predicate exists here -- deriving it deductively would require
% exporting the ROW UNIVERSE per principal, a differential that scales with ledger size rather
% than principal count (a sizing commitment that deserves its own decision, not a smuggled O(rows)
% default). Until lifted, the boundary filter's row-level behavior is witnessed by its OWN fixture
% family; this twin binds SURFACE granularity only.
