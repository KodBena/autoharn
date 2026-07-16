% ==== ledger EDB: target 's37rev' -> toy.s37rev.ledger
% ==== emitted: ['amends', 'answers', 'enacts', 'entry', 'supersedes']
% ==== DEFERRED regards: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_verdict: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED review_independence: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED obliged: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED acts_for: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
% ==== DEFERRED agent_class: kernel-shape lineage (regards + kernel.principal present) carries this family, but it is NOT emitted this increment (no T_now consumer yet) -- emission DEFERRED; require() refuses, never a silent empty
entry(1,1784186610,work_opened,none,open,none).
entry(2,1784186610,work_opened,none,open,none).
entry(3,1784186610,work_opened,none,open,none).
entry(4,1784186610,work_opened,none,open,none).
entry(5,1784186610,work_opened,none,open,none).
entry(6,1784186610,work_opened,none,open,none).
entry(7,1784186610,work_claimed,none,open,none).
entry(8,1784186610,work_closed,none,open,none).
entry(9,1784186611,work_claimed,none,open,none).
entry(10,1784186611,work_closed,none,open,none).
entry(11,1784186611,work_claimed,none,open,none).
entry(12,1784186611,work_closed,none,open,none).
entry(13,1784186611,work_claimed,none,open,none).
entry(14,1784186611,work_claimed,none,open,none).
entry(15,1784186611,work_opened,none,open,none).
entry(16,1784186612,work_violation_disposition,none,open,none).
entry(17,1784186612,work_violation_disposition,none,open,none).
entry(18,1784186612,work_violation_disposition,none,open,none).
entry(19,1784186612,work_opened,none,open,none).
entry(20,1784186612,work_violation_disposition,none,open,none).
entry(21,1784186613,work_opened,none,open,none).
entry(22,1784186613,work_violation_disposition,none,open,none).
entry(23,1784186622,work_opened,none,open,none).
entry(24,1784186622,work_depends_on,none,open,none).
supersedes(15,1).
supersedes(19,5).
supersedes(21,6).

% ==== ledger EDB: target 's37rev' -> toy.s37rev.ledger
% ==== emitted: ['work_base', 'work_discharge', 'work_parent', 'work_review_disposition', 'work_violation_disposition']
work_opened(comp1,1).
w_open(comp1,1).
work_opened(c1,2).
w_open(c1,2).
work_opened(c2,3).
w_open(c2,3).
work_opened(c3,4).
w_open(c3,4).
work_opened(c4,5).
w_open(c4,5).
work_opened(c5,6).
w_open(c5,6).
work_opened(comp1v2,15).
w_open(comp1v2,15).
work_opened("c4--via-comp1v2",19).
w_open("c4--via-comp1v2",19).
work_opened("c5--via-comp1v2",21).
w_open("c5--via-comp1v2",21).
work_opened(cyc1,23).
w_open(cyc1,23).
work_parent_edge(c1,comp1,2).
w_parent_e(c1,comp1,2).
work_parent_edge(c2,comp1,3).
w_parent_e(c2,comp1,3).
work_parent_edge(c3,comp1,4).
w_parent_e(c3,comp1,4).
work_parent_edge(c4,comp1,5).
w_parent_e(c4,comp1,5).
work_parent_edge(c5,comp1,6).
w_parent_e(c5,comp1,6).
work_parent_edge("c4--via-comp1v2",comp1v2,19).
w_parent_e("c4--via-comp1v2",comp1v2,19).
work_parent_edge("c5--via-comp1v2",comp1v2,21).
w_parent_e("c5--via-comp1v2",comp1v2,21).
work_claimed(c1,7).
work_claimed(c2,9).
work_claimed(c3,11).
work_claimed(c4,13).
work_claimed(c5,14).
work_closed(c1,shipped,8).
w_closed(c1,8,1).
w_disposition(8,deferred).
work_closed(c2,shipped,10).
w_closed(c2,10,1).
w_disposition(10,deferred).
work_closed(c3,shipped,12).
w_closed(c3,12,1).
w_disposition(12,deferred).
work_witness_present(8).
work_witness_present(10).
work_witness_present(12).
work_depends(cyc1,cyc1,24).
w_dep_e(cyc1,cyc1,24).
work_dep_type(24,informs).
w_composite(comp1).
w_vdisp(orphaned_by_retraction,2,16).
w_vdisp(orphaned_by_retraction,3,17).
w_vdisp(orphaned_by_retraction,4,18).
w_vdisp(orphaned_by_retraction,13,20).
w_vdisp(orphaned_by_retraction,14,22).
w_vdisp_resolution(16,retired).
w_vdisp_resolution(17,retired).
w_vdisp_resolution(18,retired).
w_vdisp_resolution(20,reissued).
w_vdisp_resolution(22,reissued).
w_vdisp_witness_present(20).
w_vdisp_witness_present(22).
w_vdisp_witness_in_force(20).
w_vdisp_witness_in_force(22).
