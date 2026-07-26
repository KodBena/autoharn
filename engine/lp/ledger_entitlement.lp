% ===========================================================================
% ledger_entitlement.lp -- the s60 entitlement-enforcement ASP twin (design/
% FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 item 2: "the ASP twin ships in the SAME delta... not
% filed as pairing debt"). Derives reaches_genesis/1, the independent SECOND derivation of
% kernel/lineage/s60-entitlement-enforcement.sql's SQL function
% principal_authority_chain_reaches_genesis(pid) -- ./judge holds the SQL/ASP differential in
% AGREE on this delta's fixture (seen-red/s60-entitlement-enforcement/).
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
