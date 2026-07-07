1. ordering
2. resources and tools (esp. underutilized)
3. min unsat core
4. obligations and violations (deontic concerns)
5. alethic concerns
6. defeasible reasoning
7. doxastic discrimination?
8. auditability
more verbosely
1. (ordering)
    * ordering of objectives (may not start work on variant surface before adapter/port contract is finished)
    * ordering mandates (e.g. must read ADR, must apply out-of-frame review when appropriate after work is done)
2. (resources and tools)
    * know when to reach for it; examples already abound in chocofarm, which uses
      cvxpy (cost-constrained c-optimal SOCP allocation ), ortools (declarative mapping and enumeration of hyperparameters)
      z3 (model building for debugging/attributing an apparent metastable convoy in an inference server for an
      AlphaZero-like application)
    * know when to reach for it even when the environment doesn't currently have them (collaborator may assume it's not there
      and therefore not to be used, which is in violation of professional duty (e.g. ADR-0013, or just common sense))
3. (min unsat core)
    * e.g. resolving the problem in a python virtual environment version collission; could even result in something proactive like
      actually uninstalling the offenders and patching, then installing a version that doesn't violate.
4. (deontic concerns)
    * obvious, but for example don't leave the git tree in a broken state
5. (alethic concerns)
    * possibly application to default reasoning under weak guidance to infer maintainer intent (probably specious?)
6. (defeasible reasoning)
    * ???
7. (doxasticism)
    * may be out of scope, but, hearkening to https://en.wikipedia.org/wiki/Doxastic_logic#Types_of_reasoners it
      may provide a taxonomy for observed thought pattern; merely observational, probably also specious.
8. (auditability)
    * generic and ubiquitous concern, overlaps with (2); have used psql, redis, regularly we store markdown artifacts in the
      repository.

---

Another concern, briefly: unless I misremember, some document /home/bork/w/vdc/1/claude_harness/docs/research made a,
to me, somewhat poignant remark about reifying abstract boundaries (I may be wrong) for the purpose of auditability, for example
a work unit is logged and it's discharge is logged in a separate row (possibly a separate table; but abstractly, as a separate entity altogether. I might confabulate so
don't draw any conclusions from what I say). It may be useful as a conceptual model even if the reification is only denotational (e.g. in the sense that there is an abstract
schema for mapping a separate table to a column, e.g. in SQL parlance using joins vs denormalizing tables).

On a side-note: early in this project, some agents focused heavily on trying to bend every problem into an SQL solution. Don't do that -- this is as much a practical project
as a research project to see what the practical results of the grayhairs' intellectual output for the past 60 years might lead to. Even without that caveat, a well-written CLP(FD)
can be a whole lot more elegant than an SQL query -- and it provides intellectual stimulation, which now that I think about it is probably the primary reason for
doing this in the first place.
