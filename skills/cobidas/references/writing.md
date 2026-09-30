# From evidence to manuscript text

## The compilation contract

Use this sequence: **scope → actual facts → evidence reconciliation → claim plan → prose → reverse audit → investigator review**. Do not ask the language model to reconstruct an entire analysis from a folder name or familiar software stack.

The main methods is a scientific explanation; the supplement is a reproducible specification; the evidence index is an audit trail. They are complementary views, not three competing narratives.

## 1. Freeze the reporting target

Select the exact manuscript analyses, participant/run membership, output hashes and analysis revisions. Separate primary, exploratory and sensitivity analyses. Run the helper audit and retain its digest. If any evidence/configuration/current fact changes, regenerate the audit and recheck the draft. Do not edit an old paragraph and retain an old provenance digest as if it still describes the same analysis.

An actual fact is eligible only when it is current, supported and not inference-only. Execution facts require appropriate completion/validation evidence. `not_applicable` closes an applicable-field decision only with a reason; it is not necessarily a sentence to include in the paper. Unknowns and conflicts go into gaps, not polished assertions.

## 2. Plan atomic claims

Create a claim plan with the intended section, claim, fact IDs, analysis scope and relevant method citations. Paragraph-level references are a practical minimum; split compound claims into sentences when their evidence differs. A citation to a software paper and a pointer to a run's configuration serve different purposes and both may be needed.

Check each numeral and qualifier. “All runs”, “independently”, “jointly”, “predefined”, “manually”, “corrected”, “nested” and “unbiased” each assert something that needs evidence. A small unverified adjective can change the scientific meaning of an otherwise accurate paragraph.

## 3. Allocate detail rather than deleting it

| Main methods | Supplement | Reproducibility archive, usually not prose |
|---|---|---|
| Analysed sample, major exclusions, design | Cohort flow by analysis, missingness and exceptions | Authorized inclusion/exclusion membership and derivation code |
| Scanner/sequence and essential timing/geometry | Complete acquisition parameter sets, variants and counts | Resolved metadata plus inherited-source index |
| Actual preprocessing and denoising strategy | Exact confound columns, censor rules/counts, transform variants | Configurations, receipt/logs, masks, vectors and output identities |
| Model, contrast, dependence and inference | Full model/coding/contrasts, search family, main effects behind reported differences, secondary analyses | Design matrices, fitted objects, resampling assignments, unthresholded maps (shared by persistent identifier) |
| Software with exact versions/revisions and citations (RRIDs where available) | Component and environment details: OS, CPU, parallelization, workflow system (COBIDAS D.7) | Lockfile/container digest, code commit/dirty diff, resources |
| Data/code availability and material AI contribution | Access restrictions, approvals and review procedure as appropriate | Private evidence and actual review record, released only as authorized |

A short journal paragraph does not imply a short evidence record. Explicitly point to the supplement when essential detail is delegated. Do not hide a methodological limitation solely in a private archive.

## 4. Draft in scientific dependency order

Usually: participants/design → acquisition → preprocessing/QC → signal/pattern construction → first-level model → aggregation/group model → inference → availability. Combine stages where this clarifies the actual method, especially joint nuisance regression and filtering. Avoid narrating package installation, file copying or scheduler retries unless they affect interpretation or reproducibility.

Use precise active descriptions. Replace “data were preprocessed using standard procedures” with named operations and settings that matter. Replace “a mixed-effects model was used” with the response, fixed/random structure, estimator and inferential procedure. Use exact template names rather than “standard space”. Avoid claiming accuracy, robustness or state-of-the-art quality as filler.

Preserve the distinction between intended and actual methods: a preregistered exclusion criterion modified after QC is a modification, even when scientifically justified. Describe relevant changes with their rationale and timing. Present a limitation as a limitation, not a euphemism.

## 5. Use pipeline boilerplate selectively

NiPreps tools write runtime-dependent methods/citation boilerplate [F1, F2]; see [integration.md](integration.md#fmriprep-and-other-nipreps) for where fMRIPrep puts it. Import the actual run's text and bibliography as evidence leads. Confirm relevant software, branches and parameter changes, remove irrelevant procedures, and add downstream steps the pipeline did not perform. Do not copy a previous project's boilerplate or assume that every subject took the same fallback path.

Preserve substantive method citations and attribution. The helper does not verify bibliography metadata or whether a cited paper describes the exact method; check citations against official records. Do not import fabricated references from sample documentation.

## 6. Reverse audit

For each sentence ask: What exact observation supports this? Does the scope match? Is the software/version correct? Was the operation performed or only planned? Are units and numbers correct? Does “all” conceal exceptions? Is the operation order true? Does the wording claim a stronger inference than the test supports?

Then audit the other direction: for each applicable reporting item, where is it covered in main text, supplement or an approved persistent resource? Missing information and inapplicability need explicit decisions. A high count of recorded fields does not prove the manuscript contains them.

The helper emits a draft plus a claim-evidence table and paragraph-coverage gaps. It verifies identifiers and source integrity, **not semantic entailment**. Human/agent reading against the actual records is indispensable. Do not assume a paragraph is true merely because it references a valid fact ID.

## 7. Example: a narrow synthetic claim

Evidence says that one declared analysis branch used a 6-mm Gaussian smoothing kernel after resampling to its stated volumetric template. Another branch is unsmoothed. A permissible sentence is: “For the univariate analysis, the resampled BOLD images were smoothed using a Gaussian kernel with a full width at half maximum of 6 mm.” The template identity and software citation belong in the same paragraph or adjacent acquisition/preprocessing text, backed by separate records.

An impermissible compression is: “All functional data were spatially normalized and smoothed using standard settings.” It changes the scope, loses parameters and introduces an unverified normative claim. The 6-mm value here is illustrative, not a recommended default.

## 8. Deliver and review

Always label mechanically generated drafts as drafts. List material unresolved items in the handoff. The investigator reviews the exact current text and limitations; record the approver and approved document digest through the project's review mechanism. Do not let an agent attest that a human reviewed something unless that approval actually occurred.

A completed audit can say “COBIDAS-aligned reporting audit, MRI report v1.0; scope: …; unresolved items: …”. Do not say “COBIDAS certified”, or infer scientific validity from coverage. For a full formal checklist use the frozen official Appendix D mapping, not the local field inventory.
