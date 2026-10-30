# Quiet runs and protected evaluations

Read when a benchmark, shared host, GPU, cluster allocation, or protected
evaluation needs coordinated use. Ordinary work does not require this ceremony.

Before a quiet run, record in the existing Mote coordination record:

- Resource and runner; exact code, data, and configuration.
- Expected window and the interference prohibited during it.
- Every known worker whose running or planned work could interfere.
- Start conditions, completion/cancellation, and explicit release condition.

Mark a request as proposed until participants agree. A proposal alone does not
reserve the resource. If it lapses before agreement, withdraw or re-propose it
with fresh timings and acknowledgements. Honor an agreed window even before
the measurement starts.

Obtain explicit acknowledgements from those workers before starting. Their
acknowledgement covers jobs already launched as well as future commands. Check
actual resource conditions: acknowledgements alone do not prove the host is
quiet. Do not cancel another worker's job or treat stale presence as clearance.
An unavailable participant blocks this run unless an authorized alternative
establishes isolation. Continue independent work where possible.

New workers read and honor active windows before launching work. During the
window, respect restrictions on builds and tests as well as benchmarks. Work
within permitted resources or park. The runner records completion or
cancellation and explicitly releases the window. A proposed end time is not a
release. An overrun requires an updated agreement; if the runner disappears,
inspect the actual job/resource state and use the existing recovery procedure
before declaring the resource free.

Record suspected interference and qualify the affected measurement; repeat
only when justified. Preserve failed reports and exact configurations. Keep
implementation, compatibility, accuracy, and performance claims separate.
Development results cannot substitute for gate results. Do not expose protected
results without authority, tune on a holdout, or silently redefine a failed
acceptance condition. Start protocol trials with a small development benchmark,
not a consequential frozen-suite run.
