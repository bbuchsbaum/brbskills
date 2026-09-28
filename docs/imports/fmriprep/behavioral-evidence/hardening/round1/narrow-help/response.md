**T1w vs fsnative**

They are different kinds of output, not two names for "native space."

- **`T1w`** is volumetric (NIfTI). The BOLD data are resampled into the subject's anatomical reference. That reference is built by fMRIPrep itself. It is not necessarily on the exact grid of any one original T1w file, and it may be an average over several T1w images or sessions. Files are named `space-T1w`. This is also different from BOLD-native output, which stays on the functional run's own grid.
- **`fsnative`** is a surface output (GIFTI). It samples the BOLD signal onto the subject's own FreeSurfer cortical surfaces, one file per hemisphere (`hemi-L`/`hemi-R`, `space-fsnative`). It needs surface reconstruction. It is not a volumetric native-space option, and you can't use it as a stand-in for `T1w` in a voxelwise analysis.

In short, `T1w` gives subject-space volumes and `fsnative` gives subject-space cortical surface vertices. Request `fsnative` only if your downstream analysis works on surfaces.

**Does `res-2` mean 2 mm?**

Not always. `res-` is an index into the template's list of resolutions in TemplateFlow. It is not a voxel size in millimetres. For some templates, index 2 happens to be 2 mm, but that is a convention of those templates, not a rule. It can differ for other templates and cohorts. To check a given output:

- look up that template's resolution entries in its TemplateFlow `template_description.json`, or
- read the voxel size from the output header (for example `nib.load(f).header.get_zooms()` or `fslinfo`).

Two related points:
- The template name matters as well as the grid. `MNI152NLin6Asym` and `MNI152NLin2009cAsym` are different templates, so `res-2` in one is not the same image as `res-2` in the other.
- The resolution you request for outputs only sets the grid the results are written on. It does not set the resolution used for registration.

Option spellings and output behaviour change between fMRIPrep releases. If you're working with a specific run, check `fmriprep --help` for your installed version and read its output headers instead of relying on this general description.
