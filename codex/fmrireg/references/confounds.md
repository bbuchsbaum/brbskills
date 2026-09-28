# Confounds and volume alignment

Inventory before selection. Use `bidser::confound_set("motion24")` and
`read_confounds(..., cvars=...)` rather than private constants or hand-maintained
version-specific column lists. This named-set call is a public selection interface;
it does not certify that every intended regressor exists and is usable. Save the
resolved names, source file/metadata, transformations, missing-value handling,
cleaned columns, dimensions, rank and scaling for each run.

The reviewed read_confounds defaults include `clean="zero_variance"` and
`na_action="leave"`; inspect the installed method to control these deliberately.
Do not use implicit cleaning to disguise changes to the requested model. A leading
NA in a derivative column is distinct from a missing signal midway through a run.
Never blanket drop_na(): it destroys volume alignment. Use a documented boundary
convention for leading derivatives and an approved strategy for other missingness.

Motion, tissue signals, CompCor, high-pass cosine terms, global signal, PCA-derived
confounds, nonsteady-state spikes, and censoring each have different implications.
A package README's favored denoising strategy is not a universal task-GLM default.
Task-correlated nuisance and adaptive PCA can remove the signal of interest;
inspect the combined design and retain the exact selection/estimation recipe.
Do not double count cosine/high-pass terms and an additional drift basis without
checking overlap. Protect run-specific intercepts and drift boundaries.

Record whether volumes are retained, masked/weighted, spike-modeled or actually
trimmed. A motion summary threshold is an explicit analysis/exclusion policy,
not an automatic diagnosis. No universal FD cutoff is imposed by this skill.
Plot motion alongside event timing: run averages can hide peaks or task-related
motion. Record motion units, any FD convention and derivative boundary treatment.
Use the plot to assess confounding and QC, not to invent a censoring rule after
seeing the effect maps.
Freeze any participant/run exclusion rules before examining effects. Never exclude
an individual simply because removing them increases a target statistic.

For manual bindings, confounds must be explicitly ordered to the selected scans,
with per-run rows matching stored volumes and the analysis volume mapping. Escape
and anchor identifiers when a legacy accessor uses regex; prefer exact query
paths and explicit local reads for selection. Preserve a row-alignment audit.

In the source-reviewed typed API, `noise_spec(censor=...)` only changes AR estimation/whitening, not the regression observations, and is inert for iid noise. Do not label this option alone as GLM scrubbing.
