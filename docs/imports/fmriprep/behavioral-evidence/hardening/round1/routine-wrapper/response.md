# Next pilot: preparation with the installed launcher

Your existing approval covers this pilot, so I won't ask you to confirm it again. The steps below prepare the job up to the point of submission. **I have not submitted anything.** Submitting is a separate action. It happens after the checks in section 3 pass, and only one actor (you or me, not both) should submit and handle retries.

## 1. What I'm treating as already settled

These come from the context you gave me. I did not observe them in this session, so each needs a pointer to its record:

- **Data:** valid single-echo adult BIDS. It matches a validated snapshot, so validation can be skipped, but only because the snapshot identity and validator version recorded for it match this input.
- **Recipe:** approved. The pilot must not change output spaces, reconstruction, anatomical reference, SDC/STC policy, template or fMRIPrep version.
- **Launcher:** a verified Apptainer/Slurm profile. I treat this as a candidate. It is certified only if the launcher revision, image, modules, mounts and node pool are unchanged since it was verified.

## 2. Preparation steps (run on the target cluster, not here)

```bash
# a. Identify the installed launcher and read its real interface
which fmriprep_launcher.py; git -C <launcher_repo> rev-parse HEAD   # or package version
fmriprep_launcher.py --help
fmriprep_launcher.py print-cmd --help
fmriprep_launcher.py slurm-array --help

# b. Effective configuration. The system, user, project and explicit INI files are layered on top of each other.
#    Record every source file and its hash. Do not re-initialize over your files.
#    In the project/explicit INI, set every approved scientific option (output spaces,
#    reconstruction, skip-validation, --notrack) instead of relying on example defaults.

# c. Render the pilot command and compare it with the frozen recipe
fmriprep_launcher.py print-cmd ...            # pilot subject(s) only
#    Any APPTAINERENV_*/SINGULARITYENV_* prefix is an environment assignment, not argv.
#    Record it in the environment map separately from argv. Do not eval.

# d. Render the Slurm bundle into a new, authorized, absolute directory
JOB_DIR=/abs/campaign/pilot-<attempt_id>/bundle
fmriprep_launcher.py slurm-array --script-outdir "$JOB_DIR"
```

Then inspect the generated script, manifest, subject list and path mappings:

- **Subjects:** the subject list contains only the pilot subject(s).
- **Concurrency:** set the number of subjects that run at once (M) explicitly. In this launcher it can default to the number of subjects assigned per task (B). Check that M ≤ B.
- **Resources:** per-subject nprocs and memory are separate from the Slurm task totals. The task should request at least M × nprocs CPUs and M × per-subject memory plus headroom, within your approved resource limits.
- **Paths:** every path-valued argument (BIDS, output, work, license, TemplateFlow, filter or config files) has a mount and resolves correctly inside the container. The launcher's extra options do not add bind mounts on their own.
- **Work and HOME:** each subject gets its own work directory and writable HOME. The scheduler log directory exists before submission.
- **Image:** the image in the script is the pinned one, identified by digest or path plus hash.
- **Tracking:** `--notrack` (or the project's approved telemetry setting) is present.

**e. Records.** Write `plan.json` (unchanged scientific ID) and `execution.json`. The execution record references the rendered script and manifest with `{"$file", "sha256"}` entries. Then run:

```bash
python <skill>/scripts/records.py fingerprint plan.json
python <skill>/scripts/records.py fingerprint execution.json
python <skill>/scripts/records.py check plan.json execution.json --artifact-root /abs/campaign --scope pilot
```

This check only confirms that the records are internally consistent and bound to the approval. It does not show that the job is ready to run.

**f. Submission intent.** Before `sbatch`, write down the attempt ID, a unique submission token, cluster, owner, time, plan and execution IDs, and the script hash. Capture the returned job ID straight away. If that acknowledgement is lost, reconcile against the queue and accounting before any resubmission.

## 3. Evidence I still need before I can call it ready to submit

1. **Which pilot is "next".** I need the pilot's subject ID(s) and the acquisition, fieldmap/SDC or anatomical-reference branch it covers that earlier pilots did not. If it repeats a branch that is already covered, show me that branch's recorded pilot evidence; if nothing that pilot depended on has changed, it may make this run unnecessary.
2. **The authorization record itself.** I need the source of the approval and its limits: target cluster, participants, resources and concurrency, retry budget and destination. I will check the rendered bundle against those limits.
3. **Launcher identity and configuration.** I need the installed revision, `--help` output, and the full set of layered INI files with their effective values, compared against the recipe. It must also match the revision that the verified profile was built on.
4. **Container image.** I need the pinned image path and digest or hash, and in-container `fmriprep --version` from a compute node.
5. **A compute-context probe.** This means a short job through the same partition, modules, Apptainer binds and account as the pilot, showing:
   - the CPU and memory actually allocated;
   - read access to the BIDS data (including symlink targets), the license (visible, not printed) and TemplateFlow;
   - create and delete of a test file in the output, work, log, tmp and HOME/cache directories;
   - that the required template files are real files, not empty directories or annex links;
   - no unplanned network use.

   If the profile's recorded probe predates any change to the image, modules, paths or node pool, it has to be rerun.
6. **Snapshot equality.** I need proof that the BIDS snapshot being mounted is the validated one: the dataset version or checksums, not just a matching path.
7. **Derivatives and locks.** I need the state of any existing output or work directories for the pilot subject(s): no live writer, and no incompatible earlier derivatives or FreeSurfer outputs.

Once 1–7 are in hand, the bundle can go to the single designated submitter under the existing pilot approval. After the pilot I'll report process status, expected outputs, the QC review and publication separately. A clean exit or a `.ok` marker only means the process succeeded; it doesn't show the outputs are complete or that the pilot passed QC.
