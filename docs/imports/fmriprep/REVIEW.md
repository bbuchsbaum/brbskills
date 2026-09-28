# fMRIPrep skill: import evaluation and implementation plan

Reviewed 2026-09-28. This is the original preparation plan. Implementation is now
complete locally; see [implementation and evidence](IMPLEMENTATION.md).

## Outcome and scope

Build one independently installable `fmriprep` skill in brbskills that preserves
preprocessing intent across an optional rriscripts launcher, direct execution,
and optional site guidance. This first pass preserves and evaluates the supplied
material and defines the implementation and its acceptance evidence. It does not
install a skill, change rriscripts, submit jobs, or qualify a compute environment.

The source is promising but should not be published unchanged. Its strongest
features are the scientific/execution boundary, inheritance-aware BIDS inspection,
version-aware semantics, and explicit separation of process completion, output
verification, QC, and publication. Keep those. Spend implementation effort on
verifiable contracts and realistic fixtures, rather than a universal launcher.

## Organized inputs

- [original/](original/): all 18 supplied files, byte-preserved, including the
  original design, skill, examples, references, helper, tests, and reported results.
- [original-manifest.json](original-manifest.json): archive SHA-256, per-file
  SHA-256 and size, and comparison with the separately supplied DESIGN.md.
- [VALIDATION.md](VALIDATION.md): checks actually performed in this review.

The separate DESIGN.md is byte-identical to the archived version. No redundant
copy is needed. `original/` is historical input, not the maintained implementation;
its instructions, timestamps, and test claims are attributed to that input.
The archive contains no license file; do not invent upstream license provenance.

Keep the original outside `skills/` and `collections/*/skills/`, which are the
builder's discovery roots. This prevents a draft from becoming an installable
product. Existing unrelated edits in this shared checkout remain untouched.

## Architecture decisions

**Author at `skills/fmriprep/`.** The fmri-workbench collection currently copies
all its shared resources into every member. Putting fmriprep there would import
analysis-specific material and potential filename collisions, including
`references/execution.md`. A standalone root skill is already supported by the
builder and suits preprocessing use outside this particular analysis stack.
Add an optional handoff from `fmri` later; do not require either the workbench or
Alliance for preprocessing.

**Use three records for execution work, not every conversation.** A narrow flag
explanation or diagnosis should not trigger a new BIDS survey, interview, or pilot.
Planning produces a partial plan with explicit unknowns. A launch requires a
resolved execution record and durable attempt evidence. Reuse project state and
existing authorization; the records describe authority rather than grant it.

**The agent remains the adapter.** Keep provisioning, runtime, scheduling, and
storage independent. Document the evidence a provider returns; do not build a
plugin registry, fleet scheduler, mandatory subagent protocol, or JSON-to-scheduler
compiler. An optional site skill can be read in the same session. Separate-agent
execution is not a prerequisite. One identified actor owns submission and retry.

**Qualification is scoped and reusable.** A matching, evidenced pilot can cover
subsequent runs in the same acquisition/execution scope; avoid automatically
repeating it for every invocation. Document what changes invalidate that coverage.
Resource-only changes still require appropriate execution checks, while changes
to methods, software, selected data, or requested products revise the science.

## Findings that affect implementation

| Priority | Finding | Required change |
|---|---|---|
| High | Adapter warnings are pinned to an older rriscripts revision. | Rebase the compatibility table on inspected code and qualify each claim by revision and evidence. |
| High | Hashes and approval fields exist only as examples; their meaning is unspecified. | Define exact identity inputs, canonical encoding, external referenced-file identities, and approval provenance before depending on hashes. |
| High | A receipt records a job ID but lacks a complete durable submission-intent/reconciliation contract. | Persist attempt/token, target cluster, owner, time, script identity and uncertain state before invoking submit; reconcile before retry. |
| High | The 18 scenarios contain setup/expected prose but no runnable evidence fixtures or scoring procedure. | Add synthetic inputs, permitted actions, captured outputs and critical failure criteria; distinguish helper tests from model and live execution evidence. |
| Medium | The entrypoint applies a full operator procedure too broadly and repeats safeguards across references. | Route explanation, planning, execution and recovery by task; aim for the repository's roughly 600-word entrypoint preference without removing essential constraints. |
| Medium | The probe bounds subprocess time and displayed output, but captures full output in memory and does not establish descendant-process cleanup. | Add adversarial fake-tool checks; bound capture/process lifecycle or narrow the promise. Keep version execution opt-in and retain the warning that the helper is not a sandbox. |
| Medium | Caller-declared compute context remains unverified, but readiness is represented as false. | Prefer an explicit unknown/not-assessed status where appropriate; separate failed checks, observations and qualification. Never promote host detection to compute proof. |
| Medium | Optional-provider evaluation says to delegate whenever an Alliance skill exists. | Require relevant site scope and availability; allow same-session use. An installed provider is neither an entitlement nor permission to submit. |
| Medium | Privacy guidance does not explicitly compile a telemetry policy on direct routes. | Resolve network/telemetry policy and check the selected version's controls; the launcher currently includes `--notrack`. |
| Medium | QC is correctly required but the review decision is underspecified. | Record reviewer, evidence, inspected products, flags, pass/hold/fail decision and branch-release consequence; unavailable visual review stays pending. |

### Current launcher evidence

Read-only inspection of the local checkout at
`747775e3da01e3a86e0c7e9462d9fa0c381e2715`, principally
`fmriprep/fmriprep_backend.py`. That file is unmodified locally; other checkout
files are dirty. This is not a claim about current GitHub HEAD or live behavior.
The supplied reference used `acb0a384a8aebcf9ea3b1b57d526478ad1681dc8`.

- `build_common_cli` now shares subject-independent application arguments.
- `load_cli_base` reconstructs CLI arrays inside child functions, including the
  fmriprep-docker branch. The old extra-argument splitting/exported-array warnings
  must not be presented as current defects. Existing backend tests include fake
  runtime execution coverage; they were inspected only in this review.
- Both direct and batch fmriprep-docker construction still omit an explicit image
  argument. Direct construction still emits a single `NAME=value` token after
  `--env`; compatibility must be checked against the installed wrapper CLI.
- The built-in module setting still inserts `module load singularity`.
  Preflight still checks host paths and selected options, not compute readiness.
- The direct Singularity command can contain a leading environment assignment
  token. A list returned by this wrapper is not automatically suitable as
  `subprocess.run(argv)`; inspect caller semantics and separate environment first.

Do not make upstream fixes a prerequisite. Use only demonstrably faithful routes
or bypass them with an equivalent direct payload. Keep upstream repairs a separate
work item, not hidden scope inside skill authoring.

### Scientific source spot-check

The official [usage page](https://fmriprep.org/en/stable/usage.html) currently
identifies its CLI as 25.2.5 and exposes version-sensitive anatomical-reference,
derivative-reuse and telemetry controls. This supports the version-checking rule,
not selecting 25.2.5 for every study. The [spaces reference](https://fmriprep.org/en/stable/spaces.html)
supports preserving template/grid distinctions. The
[NiPreps Singularity guidance](https://www.nipreps.org/apps/singularity/)
supports checking container HOME/cache and offline TemplateFlow access.
These are spot-checks, not a full scientific audit of all six supplied references.
Finish versioned source review during implementation, including BIDS inheritance,
fieldmap associations, output semantics and multi-echo handoff.

## Proposed maintained file layout

```text
skills/fmriprep/
  SKILL.md                         task routing, core workflow and invariants
  agents/openai.yaml               Codex UI metadata; portable core unchanged
  references/
    bids-and-decisions.md          inventory, exceptions, proposal, scoped choices
    semantics.md                   consequential choices and version boundaries
    execution.md                   provider evidence, paths, resources, qualification
    records.md                     small record contract and identity semantics
    rriscripts.md                  revision-bound capability checks and fallback
    operations.md                  ownership, recovery, QC and downstream handoff
    sources.md                     primary sources and review provenance
  assets/
    plan.example.json
    execution.example.json
    receipt.example.json
    preferences.example.json
  scripts/probe_host.py             bounded host observations only
  tests/
    test_probe_host.py
    test_records.py                 if a small deterministic record helper is added
    evaluation-cases.md
    fixtures/                      synthetic BIDS metadata and fake execution tools
    VALIDATION.md
```

Do not ship the historical design, imported test transcript or duplicate README
inside generated skills. Add a record validator/hash helper only for the concrete
contract checks below; it must not evolve into an execution engine. Preserve
JSON examples as examples and reject their placeholders for launch validation.

## Implementation sequence and acceptance

1. **Specify the small contract and route tasks.** Define required fields by
   task/state, immutable scientific content versus execution content, unknown
   values and evidence scope. Hash canonical content, excluding self-hashes,
   mutable statuses, approvals and timestamps. Keep approval evidence outside the
   hashed payload and bind it to the content identity. Reference manifests by
   identity, not only by path. Resource changes must change execution identity;
   SDC/template/software/selection changes must change scientific identity.
   Acceptance: concrete valid and invalid examples, including stale approval,
   unresolved input identity, duplicate attempts and mismatched plan/execution.
2. **Adapt and tighten the instructions.** Retain the existing domain knowledge;
   refresh version-sensitive claims and the launcher matrix. Add explicit
   same-session/provider absence behavior, telemetry and pilot reuse criteria.
   Acceptance: standalone explanation/planning works without rriscripts or
   Alliance; execution limitations cause precise blockers or faithful fallback.
3. **Harden helpers and executable fixtures.** Retain the 13 passing tests and add
   noisy/hanging executable, malformed input, protected-path and cleanup cases.
   Use fake executables that record actual argv/env to compare wrapper and direct
   payloads, including spaces and shell metacharacters. Fake scheduler jobs must
   remain local. Acceptance: no implicit launch/install/network activity; failures
   preserve evidence; argument values survive runtime and child-shell boundaries.
4. **Run independent behavioral evaluations.** Convert the 18 supplied scenarios
   into reproducible cases; add narrow-help non-trigger, inherited config conflict,
   stale approval, already-qualified pilot reuse, and unavailable QC review.
   Run fresh Codex and Claude sessions where available, with only synthetic
   fixtures and bounded permissions. Keep some cases held out from revision.
   Acceptance: no unapproved science changes, fabricated metadata/site facts,
   duplicate submission, false qualification, or silently dropped outputs. Record
   questions/reference loads and compare with a no-skill baseline before claiming
   improvement. Missing evaluator access is an explicit unrun gate.
5. **Integrate and package.** Add root catalog discovery and optional workbench
   routing/handoff with explicit missing-skill behavior. Generate Codex/Claude
   products and run the applicable checks below. Verify each extracted package
   independently, with no sibling skill or source checkout on its path. Publish
   validation limits alongside results. Live container/site pilots remain a
   separate authorized qualification stage, never simulated by local tests.

The implementation sequence warrants the repository's progress dashboard when
started. This bounded preparation pass did not start the implementation campaign.

### Planned commands

Use the repository development environment and its current requirements. New
fmriprep test paths below are planned, not commands already run.

```bash
python -m unittest discover -s skills/fmriprep/tests -v
python scripts/skills.py sync
python scripts/skills.py check
python -m unittest discover -s tests -v
python scripts/skills.py package fmriprep
# If the workbench routing/shared handoff changes:
python collections/fmri-workbench/tools/audit_bundle.py
python -m unittest discover -s collections/fmri-workbench/tests -v
```

Run shell syntax checks on generated fixtures; run behavioral cases separately
and record model/product, inputs, outputs, tool trace and reasons for verdicts.
The source is already sufficient to begin implementation without another design
interview. The next action is contract examples and task routing, followed by a
maintained `skills/fmriprep/` source. No live cluster access is needed for that work.
