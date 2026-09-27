# Design: an evidence-led fMRI skill resource

## 1. Core choice

Build a family of skills, not a giant prompt and not another analysis framework.
The package libraries own numerical work. The agent discovers evidence, translates
the scientific intent into package-native code, exposes consequential decisions,
and checks the handoffs. The skill resource owns reusable expertise and guardrails.
The local project owns scientific decisions, provenance, and execution state.

This is deliberately different from a YAML-to-analysis compiler. `plan.json` is
an approval and state envelope; native R templates and lazy plans contain the
actual implementation. A new model or package API should not require inventing
another DSL or a general autonomous project-management system.

The current first useful scope is task-fMRI from preprocessed BOLD through group
inference and reporting, with discovery of raw BIDS and an explicit preprocessing
handoff. Existing estimates or maps can enter at any downstream stage. A request
about one formula must not create a cohort workflow or a lengthy interview.

## 2. Context-efficient packaging

The five descriptions distinguish coordination, BIDS, first-level modeling,
group inference and reporting. The main SKILL bodies are approximately 400 words
each; detailed instructions are selected by need. All skill descriptions together
are 1,087 characters in this release. These are measured text sizes, not claims
about actual model tokens, latency, or routing accuracy.

A shared operating contract prevents incompatible approval/privacy behavior.
It is read for a real analysis, not every API question. Statistical detail lives
with its package. `confounds.md` is relevant to nuisance-model choices; it is not
mandatory when asking how to export an already fitted contrast. Large logs,
voxel arrays, source trees and full cohorts never become routine context payloads.

Shared materials are copied into each leaf at build time and checked for byte
identity. This modest disk duplication is intentional: a copied `fmrireg/`
folder remains usable without its siblings. Runtime context is governed by what
the agent reads, not by how many small files are installed. A root maintainer
AGENTS.md stays small and is never copied into users' analysis projects.

Use the common Agent Skills layout. Provider-specific interface metadata goes
in `agents/openai.yaml`; Claude packaging goes in `.claude-plugin/plugin.json`.
The portable root plugin manifest follows current OpenAI guidance. Do not make
Claude-only subagent semantics or hooks necessary for basic operation. No MCP
server is needed merely to call local R packages.

Current guidance from both providers supports selective disclosure and measured
skill improvement; OpenAI's Astra guidance also warns against overconstraining
models with long mandatory itineraries. We translate that into strict scientific
invariants, flexible implementation, small entry points and explicit evaluation.
See SOURCES.md rather than embedding vendor documentation in every root prompt.

## 3. Discovery: facts before questions

Discovery is a sequence of increasingly expensive inspections. First inventory
dataset roots, derivative pipelines and entities. Then resolve applicable JSON
inheritance with provenance, inspect image headers and event/confound schemas,
and profile relevant fields locally. Finally build an explicit selected-run table
that joins the scientific acquisition to exactly one chosen representation.

The acquisition identity includes subject, session, task, acquisition, direction,
run and relevant extra entities. Representation identity additionally includes
pipeline, space, resolution, echo, description and format. Several candidate
files may be legitimate alternatives, not repeated observations. A single
selection must not double-count multiple spaces or echoes as more subjects/runs.

For each fact retain value, source path/field, resolution method, and status.
Examples: observed TR from inherited JSON; header nvols; declared pipeline
version; a documented onset origin; an unresolved mapping from `trial_type=2`
to a meaningful condition. A directory named `fmriprep` is evidence of provenance
claims, not proof of successful registration or temporal cleaning.

Build a compact three-column briefing:

| Observed | Proposed | Needs your decision |
|---|---|---|
| Available derivative families and grids | One compatible family | Choice if scientific consequences differ |
| Condition codes and counts by run | An explicit mapping | Meaning not established by documentation |
| Confound columns and missingness | Applicable saved nuisance profile | Conflicts or scientifically consequential alternatives |
| Subject/session/run structure | Independent analysis units | Cohort and repeated-measures estimand |

Never ask for a TR that is already resolved. Never infer a hypothesis, handedness
coding, treatment group meaning or a longitudinal estimand solely from filenames.
Report absent/inconsistent metadata rather than silently filling plausible values.
BIDS inheritance should be checked against the standard: a deterministic merge
order does not make an otherwise ambiguous sidecar layout valid.

Timing needs explicit treatment. Negative event onsets and zero durations can be
valid. BIDS onsets refer to the stored acquisition origin; metadata describing
discarded volumes does not justify a second shift. Removing data, spike
regressors, robust weights and AR-estimation masks are distinct operations.
Mixed TR or VolumeTiming must route to verified support, not first-value casting.

The included R inventory script is a safe first pass: it enumerates and reads
metadata/header evidence, marks candidates unselected, and never announces that
a dataset is ready for fitting. Full joining and preprocessing QC remain agent-
assisted steps with explicit evidence. The Python table profiler minimizes raw
text exposure but even aggregate summaries may need an approved data boundary.

## 4. Package-specific findings that shaped the resource

The reviewed `from_bids()` implementation sorts scans and event/confound groups
by numeric run labels and takes the first discovered TR. It accepts a single
common mask. Therefore, it is not an unconditional front door for multi-session,
multi-echo, multi-space or mixed-TR data. The skill requires explicit admission
checks; otherwise it uses `as_manifest()` with validated bindings. The helper
never returns a blanket `from_bids_certified=true` based on a few scalar checks.

The reviewed `noise_spec(censor=...)` affects AR estimation and whitening only;
it does not remove regression rows, and is inert for iid noise. This is a
specific scientific footgun that a generic fMRI skill could miss. It is in the
first-level root, focused references, and an agent-eval case.

`fmri_template()` defaults to runwise meta-estimation, whereas the standalone
`estimation_spec()` default begins with joint fitting. The generated template
wrapper therefore requires an explicit control object. Within-person run
combination and across-person population inference are never conflated.

`fmrigds` distinguishes uncertainty-weighted effects, unweighted commensurate
subject values, and evidence-only z/t/p inputs. Z-scores do not recover original
BOLD effect sizes and their variances. Runs or sessions are not extra independent
subjects. Repeated-measures reducers have narrower supported designs than an
arbitrary mixed-model formula. The plan must retain those boundaries.

`neuromosaic` reports may expose related estimate/SE/statistic maps under one
analysis identity. Its interactive embedded volumes have recoverable values.
Display thresholds and minimum cluster size are not evidence of corrected
inference. The report must carry the upstream inference contract rather than
manufacture one from whatever looks attractive in the viewer.

These are source-review findings, not tested package guarantees. Capture the
installed versions, exports and relevant signatures before use. Re-exported
functions may be documented in a dependency, and generic signatures alone do
not validate all method arguments. Package versions and commit pins belong in
the actual environment lock; reviewed file blob hashes are not a substitute.

## 5. Adaptive interview without a marathon

Two separate controls matter: explanation depth and delegated authority. Brief
feedback can coexist with strict approval; teaching feedback does not imply
permission to edit a scientific protocol. The first interaction should infer
what the user already specified, then offer modes only if useful.

| Mode | Normal target | Feedback |
|---|---|---|
| Brief | One round, at most three material questions | Recommendations, consequences and blockers |
| Standard | Up to two rounds, at most six material questions | Concise rationale for consequential choices |
| Teaching | User-directed expansions | Explain alternatives and inspect designs together |

These are interaction targets, not safety thresholds. A missing essential answer
leaves a saved blocked plan, not a guess. Avoid distributing a long questionnaire
one question at a time. Group a scientific choice with its consequences, state
what is recommended, and let a user approve a coherent bundle of choices.

A hypothetical first briefing could say:

> I found one preprocessed task, two runs per person, face/scene events, and
> matching acquisition timing. I propose face minus scene using the same
> scientific model in each person, then a population-level model. Your saved
> motion24 and B-spline drift profile applies, subject to the realized-column
> and design checks. I still need to know whether incorrect-response trials
> belong in the target contrast and whether any cohort exclusions are already
> specified. I will show a compact design/pilot review before the full fit.

The dataset facts above are illustrative, not findings from a supplied dataset.
A real briefing should also identify unresolved preprocessing, scaling or
inferential assumptions. Later turns address only new conflicts and substantive
changes. Code formatting, chunk sizes within approved resource limits and
report-layout tweaks should not repeatedly reopen the scientific interview.

Prioritize questions with high consequence and unresolved uncertainty. Observable
facts are resolved by tools, not questions. Low-impact reversible decisions use
disclosed defaults under delegated authority. Hypotheses, contrasts, cohort
meaning, unsupported designs, correction families and protocol conflicts are
material. Do not optimize the pipeline by testing many specifications and picking
the one with the most favorable result.

## 6. Preferences as conditional, inspectable data

Keep persistent preferences outside provider memory and outside SKILL.md, so the
same profile can work with Claude Code and Codex. Project and user JSON stores
carry a key, value, applicability predicate, confirmation evidence and time.
A scoped rule can say “motion24 for task GLMs using fMRIPrep,” not simply “always
motion24.” An example B-spline drift preference is not an HRF preference and
still leaves the realized basis complexity to inspect.

Precedence is: institutional/scientific constraints and locked protocol first;
then current approved analysis choices, approved project preferences, confirmed
user preferences, and finally proposed defaults. A conflict with a locked
protocol requires an explicit amendment. Within a layer the most specific
matching rule wins; equally specific incompatible rules are surfaced, not chosen
by file order. The helper returns resolved values together with their sources.

Persistence requires an explicit request or confirmation of an offer to save.
Repeated choices may justify asking once, not silently rewriting defaults. A
request to forget removes the active rule; the simple audit event retains the
operation/key/time rather than the old value. Protect or remove external backups
according to the user's local retention policy. Never store credentials,
participant-level health details, uploaded raw data or executable instructions.

On each study, bind the applicable profile into a frozen plan. A later profile
edit must not silently alter an already approved analysis. Availability and
validity checks remain mandatory: a named motion24 selection resolving to fewer
columns is not quietly equivalent to the intended set. Profile settings may
control discussion style, but cannot authorize fitting or report publication.

## 7. Plan and artifact boundaries

Keep the durable state in an analysis directory separate from immutable inputs:
`plan.json`, readable plan summary, inventory, decision ledger, capability and
environment records, reviewed R code, QC, output indices and execution receipts.
The plan has stage scope, explicit configurations, material decisions, required
checks, resource limits, data policy and digests. It is not a statistical engine.

First-level fitting uses native templates, bindings, preflight and jobs. Output
records retain acquisition/subject identity, contrast definition, estimate,
SE or variance, degrees of freedom when applicable, scaling, grid/mask and
provenance. Preserve within-person covariance where a downstream combination
needs it. Equal dimensions or equal space labels are not enough to establish
voxel correspondence: check affine, grid, resolution and mask/sample order.

Group analysis consumes those records or existing valid maps. A canonical table
has `sample, subject, contrast, beta, var`; other adapters require their exact
installed contracts. Keep participants aligned by key, not row position. Freeze
formula, factor levels, contrasts, missing-data policy, dependence structure,
spatial family and multiplicity policy. Streaming must not turn a whole-brain
correction into independent per-block corrections.

Reports consume group results plus an inference manifest. They show effect,
uncertainty, cohort coverage, exclusions and failures, not only thresholded
statistical images. Exploratory plots selected from the same significant data
are descriptive, not independent confirmations. A report-only request can omit
all first-level and group fitting while preserving these interpretation limits.

## 8. Execution, resumption and limits

Use an approved pilot before expensive cohort work, with representation from
distinct acquisition strata. Separate pilot approval from full execution. Bind
approval to code, input records and environment; substantive changes invalidate
it. The helper checks explicitly sealed files, not arbitrary transitive imports.
For full execution seal each actual input/dependency or use a separately verified
content manifest; hashing the manifest alone does not rehash its member files.

Native job failure records survive partial failure. Completed outputs need
receipts linking code/input/environment digests and output checksums; an existing
filename alone is not proof of reusable work. No scheduler-specific machinery is
required: local execution, future and exported jobs remain options under the
same scientific plan. The resource does not itself keep a remote session alive
or monitor a scheduler without an active host/controller.

Approval evidence and preference consent flags are audit aids, not security
tokens. A model capable of editing local files can fabricate a flag. Actual
host permissions, institutional policy and operating-system protections remain
authoritative. Likewise local R execution does not make a cloud interaction
local-only: stdout, errors, plots and text may cross the provider boundary.

## 9. What is implemented, and what makes a release trustworthy

This bundle implements five modular instruction entry points, self-contained
packaging, selective references, local helper code, schemas, an installer,
synthetic R templates/smokes, offline tests and behavior-evaluation cases.
The Python tests and structural audit are executed. R compatibility, the full
first-level→group→report bridge, native plugin validation, live agent behavior,
and representative scientific calibration have not been executed here.

The correct next validation sequence is concrete: run the native smokes in the
pinned R environment; add small joined-BIDS and exported-map bridge fixtures;
compare against independent numerical reference analyses; run the fourteen
behavior cases with and without skills in both hosts; then use a representative
real-data pilot with explicit review. Only afterward label a release production-
ready. Optimizing token cost comes after correctness and should use held-out
cases rather than a claim that short files alone prove optimality.
