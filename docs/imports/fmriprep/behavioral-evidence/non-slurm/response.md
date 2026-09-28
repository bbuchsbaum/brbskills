# Proposed decision: PBS execution

The supplied PBS interface supports an execution record whose submit and status
operations are `qsub script.pbs` and `qstat -f JOBID`. Its resource form is
`select=1:ncpus=N:mem=Mgb` with `walltime=HH:MM:SS`. Preserve the frozen
application argv and its environment separately in the eventual script; do not
translate it into Slurm directives.

No submit-ready `script.pbs` can be rendered from this evidence. The approved
recipe/argv, resource values, walltime, output/work paths, account entitlement,
and queue entitlement are absent. The supplied syntax does not authorize guessing
any of them. No `qsub` or `qstat` call was made.

## Questions and blockers

Obtain the approved execution values and documented/authorized PBS account and
queue entitlement. Then persist a unique submission intent/token and exact script
before one authorized `qsub` submission; retain its returned job ID for `qstat -f`.
