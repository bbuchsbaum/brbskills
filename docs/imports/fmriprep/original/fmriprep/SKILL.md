---
name: fmriprep
description: Plan, launch, troubleshoot, and verify fMRIPrep preprocessing from BIDS. Use rriscripts when suitable; otherwise use verified modules, Apptainer/Singularity, Docker, or site batch execution. Inspect data before a brief decision interview. Not for downstream denoising or statistical modeling.
---

# fMRIPrep

Act as a preprocessing operator, not a flag questionnaire. Infer observable facts,
expose consequential choices, and prove that the chosen execution route works.
The rriscripts launcher and any site-execution skill are optional accelerators.

## Read selectively

| Trigger | Read |
|---|---|
| New dataset, preferences, unresolved choices | [bids-and-decisions.md](references/bids-and-decisions.md) |
| Scientific options, versions, special acquisitions | [semantics.md](references/semantics.md) |
| New host, scheduler, module, container, or site skill | [execution.md](references/execution.md) |
| rriscripts is available | [rriscripts.md](references/rriscripts.md) |
| Launch, failure, retry, QC, downstream handoff | [operations.md](references/operations.md) |
| Need authoritative detail or compatibility check | [sources.md](references/sources.md) |

Resolve references and bundled helpers relative to this SKILL.md, not the project
working directory. Read only relevant sections; do not load the whole repository.

## Procedure

1. **Establish scope.** Locate BIDS, requested subjects/sessions/runs, existing
   derivatives, authorized compute destination, and project policy. Read existing
   preferences and plan before asking. Do not assume the agent's machine is the
   execution machine. Planning is not permission to transfer data or submit jobs.
2. **Inspect before interviewing.** Use a BIDS-aware index with JSON inheritance;
   inspect headers and a local validator report. Inventory anatomical images,
   BOLD groups/echoes, timing, SBRefs, and fieldmap associations. Summarize common
   cases plus exceptions. Classify each conclusion as observed, inferred,
   proposed, or blocked; retain its evidence. Never invent acquisition metadata.
3. **Resolve the software.** Preserve an approved project version; otherwise
   propose a tested release and immutable identity. Inspect `--version` and
   `--help` through the actual execution route; consult matching release docs
   for semantics. A filename, module name, or mutable tag is not version proof.
4. **Propose one recipe.** Show selected data, explicit spaces/grids, surface
   reconstruction choice, anatomical-reference policy, expected SDC and STC,
   output/work locations, and resource/pilot plan. Defaults are proposals, not
   user preferences. Resolve incompatibilities before presenting the recipe.
5. **Ask for deltas.** In brief mode target one round and at most three material
   questions. Never ask facts obtainable from the data or system. Ask only about
   scientific ambiguity, authorization, or a genuine blocker. Explicitly
   authorized defaults need no redundant confirmation. Essential uncertainty
   blocks affected jobs even when the question budget is exhausted.
6. **Separate science from execution.** Freeze `plan.json`; resolve a compatible
   `execution.json` as described in the execution reference. An optional site
   skill may supply that profile. Otherwise investigate the environment and
   construct a minimal adapter. Do not silently alter the scientific recipe to
   accommodate a wrapper or machine. Do not claim a JSON example is a launcher.
7. **Prove, then launch.** Verify paths, version, CLI, cache assets, license,
   writable destinations, and actual allocation inside a representative compute
   job/container. Inspect the rendered command and scheduler script. With
   authorization, run a full-quality pilot for each material acquisition branch;
   inspect outputs/QC before releasing the cohort. Record submission receipts.
8. **Verify and hand off.** Distinguish submitted, running, process-success,
   output-verified, and QC-reviewed. Check expected outputs per selected run and
   space; inspect reports, not just exit codes. Preserve provenance and publish
   derivatives/receipts before scratch expires. Export a downstream manifest.

## Invariants

- Raw data are read-only. Correct metadata only in an approved, provenance-tracked
  copy or patch; never repair ambiguity by guessing.
- Check project constraints first. Then use explicit request > approved project
  recipe > applicable confirmed preference > proposed default. Contradictions
  require resolution. Scientific changes create a new recipe revision.
- Pin software and record effective options. Do not auto-upgrade midway through
  a cohort. Check version-specific behavior rather than copying old examples.
- Validate once against an identified input snapshot; skip repeated validation
  only with recorded evidence. An example INI is not evidence of valid BIDS.
- No automatic SyN substitution, fieldmap suppression, surface disabling,
  participant exclusion, resolution change, or reuse of incompatible derivatives.
- Independent processes get distinct work areas. Never concurrently reconstruct
  the same subject's anatomy/FreeSurfer directory. Reuse requires compatibility
  checks and exclusive ownership; never erase work or stale locks blindly.
- Bound process count by the allocation, not the login machine. Verify compute
  mounts, writable HOME/tmp/cache, and all required offline assets. Keep argv as
  an array and environment as a map; do not use `eval` for quoting repairs.
- Keep private imaging, identifiers, licenses, and unrestricted environment
  dumps out of external services unless specifically authorized. Report minimal
  metadata and sanitized logs. Do not print a license's contents.
- Separate workflow facts from preferences. Save a reusable preference only on
  explicit request/confirmation; store it outside SKILL.md with scope/provenance.
- Submission uncertainty means reconcile scheduler state, not submit again.
  Infrastructure retries must not silently change scientific methods.

## Deliverables

Write artifacts outside raw BIDS: a compact inspection report; approved recipe;
execution evidence and exact command/scripts; per-attempt receipt and logs;
per-run completion/QC manifest; software-generated methods/citations. On a
blocked task, save the partial plan and the smallest actionable blocker.
