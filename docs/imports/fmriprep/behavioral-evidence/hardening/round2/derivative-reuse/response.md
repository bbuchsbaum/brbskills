I'd advise against pointing the 25.2.5 run at the old output folder or the old work directory. Neither would make the run legitimately faster, and both would put the existing 23.2.1 results at risk.

**Why not**

- **Old work directory (Nipype cache):** the cache was built by 23.2.1 under a different recipe. The workflow graph, node inputs and code all differ in 25.2.5, so the cached nodes won't produce valid hits. You get a mix of recomputation and possibly stale or incompatible state, and no reliable speedup. Treat it as a version-incompatible cache. Isolate the new attempt and leave the old cache alone. Don't delete it either; decide that under your retention policy.
- **Old output folder:** fMRIPrep reads `dataset_description.json` and warns when an output directory holds results from a different version. That warning means "choose a new output namespace." Writing 25.2.5 outputs over 23.2.1 ones would mix two versions in one cohort's derivatives. You'd end up with MNI152NLin2009cAsym files from 23.2.1 next to new files from 25.2.5, a dataset-level `dataset_description.json` that describes only one of them, and no clean provenance for either set.
- **The anatomy doesn't carry over anyway:** the new recipe uses `--subject-anatomical-reference sessionwise`. The old run built a single subject-level anatomical reference (23.2.1 has no sessionwise mode). The old anatomical outputs and template transforms are therefore a different scientific product. Feeding them in, whether by sharing the folder or through `--derivatives`, would quietly undo the approved recipe change. Also, 25.2 tracks sessions by default (`--track-sessions`) and uses session-aware FreeSurfer subject IDs (`sub-X-ses-Y`). An existing `sourcedata/freesurfer/sub-X` reconstruction won't be matched and would be redone, or worse, left behind as a confusing stray. So the step you're hoping to skip, anatomy and recon-all, is exactly the step the new recipe has to recompute.

**What I'd do instead**

1. New output namespace, e.g. `derivatives/fmriprep-25.2.5/`. Keep `derivatives/fmriprep/` (23.2.1) read-only as the prior release.
2. A fresh work directory per subject for this recipe, e.g. `work/fmriprep-25.2.5/sub-XX/`, on retained shared scratch so an interrupted job can resume from *its own* cache. That's the speedup you can actually rely on.
3. Other time savings that don't change the science:
   - pre-stage a shared, read-only TemplateFlow cache containing MNI152NLin2009cAsym and MNI152NLin6Asym res-2;
   - size CPU and memory per subject from pilot accounting;
   - run independent subjects in parallel, but never two jobs on the same subject or anatomy.
4. Pilot one representative subject (full quality, not `--sloppy`) for each acquisition branch before releasing the cohort. The version and anatomical-reference change makes this a new recipe, so the old results don't qualify it.

If you have a specific reason to reuse the old results, such as limited compute, the proper route is a scoped scientific revision, not a shared folder. For example, you could keep the 23.2.1 MNI152NLin2009cAsym outputs as they are and run 25.2.5 only for the new work. That's a recipe decision you'd need to approve explicitly, because it means two software versions in one analysis. It's not something to fall into through directory reuse.

Tell me the paths you want for the new output and work directories (or accept the names above), and I'll prepare the pilot command and preflight checks. Nothing has been run or submitted.
