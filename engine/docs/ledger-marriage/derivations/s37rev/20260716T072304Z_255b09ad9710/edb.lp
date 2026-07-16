% ==== ledger EDB: target 's37rev' -> toy.s37rev.ledger
% ==== emitted: ['amends', 'answers', 'enacts', 'entry', 'supersedes']
% ==== DEFERRED regards: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_verdict: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_independence: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED obliged: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED acts_for: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED agent_class: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
entry(2,1784186448,work_opened,none,open,none).
entry(3,1784186448,work_claimed,none,open,none).
entry(5,1784186456,work_opened,none,open,none).
entry(6,1784186456,work_depends_on,none,open,none).
entry(8,1784186467,work_violation_disposition,none,open,none).
entry(9,1784186476,work_opened,none,open,none).
entry(10,1784186476,work_depends_on,none,open,none).
entry(11,1784186477,work_violation_disposition,none,open,none).
entry(12,1784186508,work_opened,none,open,none).
entry(13,1784186508,work_depends_on,none,open,none).
entry(14,1784186508,work_violation_disposition,none,open,none).
entry(16,1784186563,work_opened,none,open,none).
entry(17,1784186563,work_depends_on,none,open,none).
entry(18,1784186563,work_violation_disposition,none,open,none).
entry(19,1784186563,work_violation_disposition,none,open,none).
entry(20,1784186583,work_opened,none,open,none).
entry(21,1784186583,work_depends_on,none,open,none).
supersedes(19,18).

% ==== ledger EDB: target 's37rev' -> toy.s37rev.ledger
% ==== emitted: ['work_base', 'work_discharge', 'work_parent', 'work_review_disposition', 'work_violation_disposition']
work_opened("probe-check",2).
w_open("probe-check",2).
work_opened("probe-dep-a",5).
w_open("probe-dep-a",5).
work_opened("probe-dep-b",9).
w_open("probe-dep-b",9).
work_opened("probe-dep-c",12).
w_open("probe-dep-c",12).
work_opened("probe-dep-d",16).
w_open("probe-dep-d",16).
work_opened("probe-dep-e",20).
w_open("probe-dep-e",20).
work_claimed("probe-check",3).
work_depends("probe-dep-a","nonexistent-antecedent",6).
w_dep_e("probe-dep-a","nonexistent-antecedent",6).
work_depends("probe-dep-b","another-nonexistent-antecedent",10).
w_dep_e("probe-dep-b","another-nonexistent-antecedent",10).
work_depends("probe-dep-c","yet-another-nonexistent-antecedent",13).
w_dep_e("probe-dep-c","yet-another-nonexistent-antecedent",13).
work_depends("probe-dep-d","dep-d-antecedent-missing",17).
w_dep_e("probe-dep-d","dep-d-antecedent-missing",17).
work_depends("probe-dep-e","dep-e-antecedent-missing",21).
w_dep_e("probe-dep-e","dep-e-antecedent-missing",21).
work_dep_type(6,informs).
work_dep_type(10,informs).
work_dep_type(13,informs).
work_dep_type(17,informs).
work_dep_type(21,informs).
w_vdisp(depends_on_unknown_slug,6,8).
w_vdisp(depends_on_unknown_slug,10,11).
w_vdisp(depends_on_unknown_slug,13,14).
w_vdisp(depends_on_unknown_slug,17,18).
w_vdisp(depends_on_unknown_slug,17,19).
w_vdisp_resolution(8,retired).
w_vdisp_resolution(11,reissued).
w_vdisp_resolution(14,reissued).
w_vdisp_resolution(18,reissued).
w_vdisp_resolution(19,retired).
