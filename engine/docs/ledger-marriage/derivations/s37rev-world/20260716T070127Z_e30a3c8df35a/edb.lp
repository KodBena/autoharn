% ==== ledger EDB: target 's37rev-world' -> toy.s37rev.ledger
% ==== emitted: ['amends', 'answers', 'enacts', 'entry', 'supersedes']
% ==== DEFERRED regards: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_verdict: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_independence: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED obliged: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED acts_for: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED agent_class: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
entry(2,1784185139,work_opened,none,open,none).
entry(3,1784185139,work_depends_on,none,open,none).
entry(5,1784185156,work_opened,none,open,none).
entry(7,1784185186,work_opened,none,open,none).
entry(8,1784185186,work_opened,none,open,none).
entry(9,1784185186,work_depends_on,none,open,none).
entry(10,1784185201,work_claimed,none,open,none).
entry(13,1784185218,work_claimed,none,open,none).
entry(14,1784185218,work_closed,none,open,none).
entry(15,1784185218,work_closed,none,open,none).
entry(16,1784185261,work_closed,none,open,none).
entry(18,1784185281,work_violation_disposition,none,open,none).
supersedes(16,14).

% ==== ledger EDB: target 's37rev-world' -> toy.s37rev.ledger
% ==== emitted: ['work_base', 'work_discharge', 'work_parent', 'work_review_disposition', 'work_violation_disposition']
work_opened("probe-a",2).
w_open("probe-a",2).
work_opened("probe-b",5).
w_open("probe-b",5).
work_opened("comp-parent",7).
w_open("comp-parent",7).
work_opened("comp-child",8).
w_open("comp-child",8).
work_claimed("comp-parent",10).
work_claimed("comp-child",13).
work_closed("comp-child",shipped,14).
w_closed("comp-child",14,1).
w_disposition(14,witnessed).
work_closed("comp-parent",shipped,15).
w_closed("comp-parent",15,1).
w_disposition(15,witnessed).
work_closed("comp-child",dropped,16).
w_closed("comp-child",16,1).
w_disposition(16,deferred).
work_witness_present(14).
work_witness_present(15).
work_depends("probe-a","never-existed",3).
w_dep_e("probe-a","never-existed",3).
work_depends("comp-parent","comp-child",9).
w_dep_e("comp-parent","comp-child",9).
work_dep_type(3,informs).
work_dep_type(9,"blocks-close").
w_composite("comp-parent").
w_vdisp(closed_but_tree_defeated,15,18).
w_vdisp_resolution(18,retired).
