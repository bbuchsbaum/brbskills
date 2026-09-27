# Timing and joins: common silent failures

## Event origin and dummy volumes

BIDS event onset zero refers to the first **stored** sample. Negative onsets are
allowed; duration zero is an impulse and positive durations are intervals.
Discard-count metadata does not instruct a second subtraction from events.
If analysis additionally removes leading volumes, record the raw-to-analysis
index mapping and shift/re-express timing exactly once. Preserve discarded events
that can still contribute HRF signal to retained samples. Out-of-run tails can be
legitimate; inspect rather than automatically deleting them.

Confirm the model's sampling convention (e.g. volume start versus slice-time
reference), and whether preprocessing performed slice-timing correction. A mean
slice time or TR/2 is not automatically correct. Verify sparse/nonuniform acquisition
support before modeling VolumeTiming as constant TR. Different per-run TRs require
separate valid sampling frames or an explicitly supported route, not first-value
or average-value substitution. Don't assume fmrireg's convenience importer handles it.

Censoring and trimming are distinct. Do not delete arbitrary rows and pretend the
remaining volumes are regularly sampled. Use an approved supported censor/weight/
spike approach and verify noise-model compatibility. Derivative confound rows,
BOLD rows and volume masks must preserve the same original index. Make leading
motion-derivative NA handling explicit, not generic drop_na().

## Keys

Canonical acquisition identity includes sub, ses, task, acq, dir, run, and any
relevant recording/part entities. Representation adds echo or echo combination,
pipeline/version, desc, space, res/den, format. Preserve every parsed entity even
if the standard examples do not list it. A within-person repeated-measures ID is
not the same as a subject ID. Use an explicit map to internal sequential block
indices while retaining original BIDS keys.

Events often omit echo, space and preprocessing entities. A correct many-to-one
join can intentionally reuse events across raw echoes, but a model generally
selects or combines echoes first. Confounds may be acquisition-level or
representation-specific depending on preprocessing. Inspect provenance; do not
assume a join projection universally. Masks have their own scope. Check row order
and lengths after joining, never zip independently sorted lists.

## from_bids shortcut admission criteria (reviewed source)

The fmrireg `R/from_bids.R` review found: scans ordered by numeric run; TR reduced
to its first value; events/confounds ordered separately by numeric run; one common
mask path; extra arguments forwarded to confounds, not scan filtering. Thus permit
the shortcut only after establishing a single unambiguous representation, unique
run numbering within each binding, constant compatible TR, complete keyed events/
confounds, and one justified aligned common mask. Explicitly restrict task/space/
subjects; do not allow space=NULL to select alternative grids.

Otherwise generate explicit bindings and `as_manifest()` using public functions.
Possible units are subject-session or separate acquisition strata; how those enter
a within-person/group model is a scientific choice. The supplied Python inventory
checker catches selected ambiguities, but its passing result is necessary only
for that limited checklist, never sufficient certification of shortcut safety.

## Validator and visual review

Run the official BIDS validator locally when available and preserve its version/
output. Inherited TSV uses the applicable file, not JSON-style row merging.
Resolve same-level sidecar conflicts instead of accepting whichever the resolver
merges last. Review preprocessing QC/registration/coverage as well as BIDS validity:
a structurally valid dataset can be unusable for a particular scientific contrast.
