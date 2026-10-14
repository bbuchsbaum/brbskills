# Architecture and value

## Preserve the point of the project

Restate the strongest credible reason this project should exist. Distinguish the
non-negotiable differentiator from optional breadth. Do not automatically replace
“beautiful, modular, fast scientific core” with “small generic CRUD application.”
Equally, a compelling vision does not excuse an unusable path to the first result.

Judge the architecture by a small number of representative workflows and changes.
For each, identify who owns semantics, state, resources, and extension boundaries.
Useful questions include whether an ordinary new operation fits existing abstractions,
whether equivalent behavior has multiple competing implementations, and whether
resource lifetimes, data movement, and failure propagation are visible.

Translate aesthetic complaints into consequences. Instead of “too many abstractions,”
show that a realistic extension requires synchronized changes to three independent
semantic authorities. Instead of “not modular,” identify a dependency that prevents a
required component from being replaced or tested independently. Additional modules or
classes are not automatically bad, and fewer files are not automatically simpler.

## Follow the seams

For the outcome under review, inspect relevant boundaries such as installation to public
entry point, API to engine, UI to model, metadata to numerical arrays, memory to durable
state, or training to evaluation. A polished screen with synthetic data and a tested
engine that is unreachable from that screen are separate assets, not an integrated
workflow. A mock is acceptable when clearly scoped; silently selecting it by default
can invalidate a real-use claim.

Where a component is shared by several outcomes, establish whether the shared contract
is genuinely the same. Similar-looking code does not justify unification when semantics
differ. A common semantic core with specialized execution paths may be preferable to
either duplication or a single overgeneralized engine; justify this from the inspected
requirements, not as an architectural slogan.

## Choose an ambition-preserving path

Compare the current implementation plus a focused fix, reuse or integration of an
existing capability, and replacement. A rewrite recommendation should identify the
specific constraint that cannot reasonably be addressed incrementally, retained assets,
migration boundaries, semantic compatibility checks, and a reversible first step.
Without that case, recommend an experiment or incremental bridge rather than demolition.

Identify missing prerequisites whose resolution opens multiple valuable workflows.
A small integration fix may matter more than several new subsystems. Describe this
causal leverage rather than assigning arbitrary numerical impact scores.

Ask what the next user should be able to do without developer intervention. For product
value or adoption claims, distinguish observed usage from presumed demand. Compare
against a credible alternative, including doing nothing or using an existing library.
Research current external alternatives only when that comparison could change the
recommendation; do not demand a market study for a focused implementation check.

## Decision framing

**Continue**: current direction is supported; name remaining bounded work.
**Focus**: the thesis remains credible, but a narrower execution sequence or shared
prerequisite should come first.
**Reframe**: change the claim, target workflow, or design because a central assumption
is contradicted or no longer binding.
**Pause the affected path**: proceeding would expose unacceptable risk or depend on
an unresolved decisive fact; name the test or decision that would reopen it.

These are recommendations, not permissions to rewrite scope or stop unrelated work.
A mixed verdict is often appropriate. State the strongest supported objection to your
recommendation and which observation would make you change it. Do not invent opposition
for balance when no substantive countercase exists.
