# Evidence model and reconstruction rules

## Three record kinds

**Fact**: one reportable property at a declared scope and phase. A value may be a scalar or a small structured object; large matrices and tables are separate evidence artifacts. A known fact has a basis and precise evidence. `phase=planned` never satisfies an actual-methods requirement.

**Activity**: a producing attempt with software identities, invocation/resolved configuration, inputs, outputs, status and validation. A successful process is not sufficient: validate expected outputs and retain the validation evidence. Keep failed and partial attempts as activities; actual execution facts may not cite them as successful producers.

**Decision**: a consequential choice, reason, decision maker/role, timing, available evidence and whether relevant results had been inspected. This is an accountable decision summary, not private model chain-of-thought. Store separate primary, exploratory and sensitivity branches.

The JSON schema describes interchange. The Python helper also performs selected integrity checks that JSON Schema cannot express, including source hashes, current heads, receipt dependencies, scope membership and stale manuscript snapshots. It is not a universal workflow engine or a semantic proof checker.

## Basis versus status

| Basis | Meaning | Permitted use |
|---|---|---|
| `observed` | Direct inspection of an appropriate artifact | Declarative claims within what that artifact establishes |
| `derived` | Deterministic calculation from identified sources | Retain source inputs and calculation/code evidence; record rounding separately |
| `documented` | Explicit study/protocol/document statement | Suitable for protocol facts, but a software manual alone does not establish execution |
| `reported` | Identified human testimony about this study | Preserve who supplied it and its limitations; never upgrade it to contemporaneous execution evidence |
| `inferred` | Plausible conclusion not directly established | Discovery lead only; excluded from declarative draft claims by the helper |

`status=known` is distinct from the basis. `status=unknown` uses `value=null` and says what was searched. `status=not_applicable` uses `value=null` and a substantive applicability reason. “No global signal regression” or “no smoothing” is a known negative, not an unknown or automatically inapplicable item. A known negative must still have evidence.

A partly recovered structured property may use `status=known`, a `value` containing **only established subdetails**, and `missing_details` naming everything still absent. For example, keep a recovered scanner manufacturer/model while recording `missing_details: ["receive_coil"]`. The audit reports `known_incomplete` and retains the gap, while permitting claims about the established subdetails. Never fill an absent component with a default or hide it in a free-text placeholder. A binding to this fact does not authorize a claim about its missing component.

`conflict`, `missing`, `stale` and `execution_unverified` are audit outcomes. They are not resolved by setting a confidence score or taking a majority vote.

## What each source can establish

An acquisition sidecar can establish recorded TE, but cannot by itself prove that acquisition metadata was correct. A model object's design matrix can establish regressors actually fitted, but a design-generation script alone cannot. A scheduler log can establish process termination, but may not establish that every participant produced valid outputs. An HTML QC report can establish that a report was generated, but not that a scientist reviewed it. A pipeline citation boilerplate can describe that pipeline's branch, but cannot establish downstream denoising.

Triangulate sources according to the claim, not a universal source ranking. For executed choices prefer receipt + resolved configuration + output metadata/model objects. For recruitment or ethics prefer the approved protocol or explicit investigator attestation. For counts derive from the selected analysis membership and exclusion table. Retain disagreement between protocol, sidecar and image header rather than declaring one always authoritative.

## Scope and provenance

Evidence pointers use project-relative paths, a locator (JSON pointer, table/column selection, line range, object attribute or report section), and SHA-256. Hash whole small files; keep large data by approved immutable dataset revision/object identifiers when hashing is impractical. Do not claim an object-store ETag is necessarily a SHA-256 digest. A directory path or mutable container tag is not a fixed identity.

A receipt should link input/output identities, code commit plus dirty-diff identity when relevant, software revision, image digest or environment lockfile, exact invocation or a hashed resolved configuration, attempt, completion and validation. Do not log secrets or all environment variables. Record selected relevant variables, hardware/parallelism and random seed policy. Seeds do not guarantee bitwise identity across hardware or nondeterministic kernels.

For derived facts retain the aggregation code and source membership. Report a range only after checking the complete set. A parameter shared by every included run is one fact plus a verified membership manifest, not 300 copies of the same prose.

## Corrections and concurrent records

A new fact can `supersede` one or more earlier facts only with the same key, scope and phase. Two unsuperseded heads are a conflict even when timestamps suggest a likely order. To resolve, inspect the sources, create a fresh fact and explicitly supersede both. Do not replace a failed activity with a success activity under the same ID.

The ledger is append-only by convention and checked by content. It is not tamper-proof, authenticated or digitally signed. Use normal version control, access controls and an immutable archive for stronger assurance. The helper's event filenames prevent accidental ID reuse; they do not make an agent incapable of deleting files.

## Retrospective studies

Preserve available originals before reconstruction. Recover the input cohort, executed pipeline identity, actual model matrices/objects and result maps first. Search old job logs, container identifiers, configuration snapshots and pipeline-generated descriptions. Record which sources were absent and what cannot be recovered.

Do not silently re-execute a current script to “verify” an old analysis: that is a new analysis revision, not historical evidence. A newly executed reproduction may support reproducibility, while leaving the original execution uncertain. For an attested legacy processing step without a recoverable receipt, the helper deliberately keeps `execution_unverified`; an investigator can report the qualified historical limitation. Do not manufacture a receipt to satisfy the tool.

## Publication boundary

The full ledger can contain study-sensitive information even without direct identifiers. Keep private participant membership, linkage and precise acquisition dates outside public text. Use authorized aggregates and pseudonymous references where needed. A hash preserves identity of an artifact; it does not anonymize the artifact. Human review should assess both factual accuracy and what may be disclosed.
