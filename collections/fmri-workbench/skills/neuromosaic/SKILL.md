---
name: neuromosaic
description: "Create neuromosaic fMRI map montages, atlas-annotated cluster reports, or interactive explorers from existing statistical outputs. Use without refitting analyses; distinguish display thresholds from statistical inference."
license: MIT
compatibility: Requires local filesystem access; R for package execution and Python 3.10+ for optional helpers.
metadata:
  version: "0.1.0"
  reviewed: "2026-09-27"
---

# fMRI reports with neuromosaic

Accept existing maps plus their inference/provenance metadata. This stage does
not require bidser, fmrireg, or fmrigds, and never refits a model merely to render
it. Read [report construction](references/reports.md) for the relevant output.
For a new report read the [operating contract](references/operating-contract.md);
verify [capabilities](references/capabilities.md) if the installed API differs.

## Establish what the maps mean

Identify quantity (effect, SE/variance, statistic, p/q), test distribution and df,
contrast/direction, spatial frame and grid, background/atlas compatibility, and
the inferential mask/correction/alpha. Follow [artifact contracts](references/artifact-contracts.md).
A name such as `z_map` is not evidence of a z distribution. Unknown correction
must be labeled unknown or exploratory, never guessed from a threshold.

Use a map manifest with `analysis_id`, `map_id`, `path`, `role`, `quantity`,
`distribution`, and `label` to group primary tests with effects and uncertainty.
`assets/report_template.R` is a source-reviewed starting function. Prefer a
static HTML report initially; PDF depends on additional rendering tools.

## Render faithfully

Show effects and uncertainty as well as thresholded statistic views. Use matched
scales where comparisons are intended, readable legends/units, valid masks and
atlas labels, and both relevant signs. Keep cluster connectivity, minimum extent,
and threshold semantics explicit. A voxel threshold plus minimum cluster size
is a display rule, not cluster-corrected inference. Never tune display choices
until an anticipated finding appears. Keep null/empty results and missing inputs
visible. Regions selected on the same statistic may have descriptive signal
plots, but those are not independent confirmatory tests.

If inference lives in an explicit rejection mask, verify that the chosen rendering
path actually respects it; otherwise create clearly labeled masked **display
copies** without replacing the original maps. Retain the full correction metadata.
Do not assume an undocumented renderer parameter accepts a q-map or rejection mask.

## Interactive and sharing decisions

Read [privacy and interpretation](references/privacy.md) before adding embedded
interactive volumes, subject-linked plots, or external sharing. The reviewed
`montage_interactive()` can embed recoverable voxel values. Local HTML and no CDN
do not make an artifact deidentified or safe to upload. Request explicit approval
for its disclosure level. Reader-adjusted thresholds are exploratory and must
not silently change the authoritative inference/report defaults.

## Validate and deliver

Inspect representative pages/panels and map alignment, labels, signs, scale,
legends, empty states, and links. When available, compare static and interactive
semantic content, not pixel identity. List all generated files and any companion
asset directory, rendering environment, input hashes, and privacy limitations.
Do not claim successful rendering from code generation alone. Return the report
and its data/inference manifest; no additional modeling or cohort interview.
