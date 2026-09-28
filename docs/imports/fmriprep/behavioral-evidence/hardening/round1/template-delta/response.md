# Plan revision: standard space changed to MNI152NLin6Asym (this study only)

Done. The recipe now uses **MNI152NLin6Asym** in place of MNI152NLin2009cAsym. This change applies to this study only. I have not saved it as a general preference, so other projects will still get their own proposal.

## Revised recipe (only the spaces changed)

| Item | Before | Now |
|---|---|---|
| Standard-space output | `MNI152NLin2009cAsym:res-2` | `MNI152NLin6Asym:res-2` (grid to verify, see item 1 below) |
| Native anatomical output | `T1w` | `T1w` (unchanged) |
| Reconstruction, anatomical reference, SDC/STC, nonsteady-state handling, quality, confounds/reports | as proposed | unchanged |

The output-space argument becomes `--output-spaces T1w MNI152NLin6Asym:res-2`, without MNI152NLin2009cAsym. I dropped 2009c because you said "instead". If a downstream consumer still needs 2009c, tell me and I will add it back as a second space. It is not free: it costs extra normalization work and storage.

## Consequences for the plan record

- **This is a scientific revision.** It changes the scientific identity: a plan record gets a new `content_id`. The old ID stays in the revision history and is not overwritten.
- **Earlier approvals do not carry over automatically.** Any pilot or cohort approval tied to the 2009c recipe does not cover this recipe, unless your original instruction explicitly allowed a template change. Your message counts as approval of the recipe change. It is not approval to launch. I will ask for launch scope again when we get there.
- Execution settings (resources, mounts, scheduler) do not change because of this, but the execution record points to the plan ID, so it also gets a new ID.

## What needs rechecking

1. **The actual grid.** For each template, `res-2` is a resolution index, not a guaranteed voxel size. On the target system, check the `MNI152NLin6Asym` TemplateFlow metadata or the header of the `res-2` template: voxel size, dimensions, and affine. Put the verified grid in the plan. Do not assume it matches the 2009c grid. The two templates are different spaces, not relabelings of each other.
2. **Template assets on the compute nodes.** If the nodes have no network access, or TemplateFlow is pre-staged or read-only, confirm that the MNI152NLin6Asym files the workflow needs are in the cache that the job actually sees. That includes the files needed for registration, not only the output grid. Record their identities in the asset manifest. A cache that was staged only for 2009c will fail, or try to download, at runtime.
3. **Pilot.** The science changed, so any pilot run under 2009c does not qualify this recipe. Run a new full-quality pilot (no `--sloppy`) that covers each material acquisition/SDC/anatomical branch. Review the normalization to MNI152NLin6Asym in the reports and outputs before releasing the cohort.
4. **Existing derivatives.** If any 2009c outputs or work directories exist, write the new run to a separate output namespace. Do not mix 2009c and NLin6Asym files in one derivative tree, and do not treat the old standard-space outputs as reusable. Native and anatomical intermediates may be reusable only after a provenance and compatibility check, not by assumption.
5. **Downstream assets.** Check every atlas, ROI, mask, or group template that later analyses will apply to these outputs. Anything defined in MNI152NLin2009cAsym needs a proper transform or a version made for NLin6Asym. Otherwise it will be misregistered. Update the handoff manifest so it names the template and verified grid.
6. **Methods text.** Update the methods and citations to name MNI152NLin6Asym, the verified resolution, and the TemplateFlow identity.

## Unaffected

Run selection, fieldmap/SDC coverage, slice timing, the FreeSurfer setting, the anatomical-reference choice, and software version stay as previously resolved. Nothing was run or submitted for this revision.
