# Proposed decision: module container wrapper

Use the supplied module entrypoint, not an additional manually constructed
Apptainer invocation: `module load prep/25.2.5` followed by the already approved
fMRIPrep argv through `fmriprep`. The supplied evidence says that this entrypoint
is `/site/bin/fmriprep`, which already calls `apptainer run /site/images/prep.sif`.
Adding a second container layer would not be justified.

No submit-ready command was rendered because this case does not supply the
approved argument vector, allocation, or path mappings. No module or runtime was
called in this exercise.

## Remaining verification

Verify in the intended noninteractive compute context: the module's effective
entrypoint and actual fMRIPrep/image identity; available allocation; translated
read/write paths; license, HOME, tmp, cache and TemplateFlow access; and required
assets. Also retain exact argv and allowlisted environment separately from the
module setup.

## Questions and blockers

Blocking inputs: the frozen approved argv and compute-context evidence above.
