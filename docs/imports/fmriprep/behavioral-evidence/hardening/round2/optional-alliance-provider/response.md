**Execution profile: not resolved yet (blocked). Nothing was submitted, and nothing was run on a cluster.**

**What I have**
- I can't find a plan in this workspace. There is no `plan.json` and no recipe. I therefore have no `content_id` to attach an execution record to, and no recipe or resource needs to check a route against.
- The `alliance-hpc` skill is available, but no site profile has been verified. The skill gives guidance and probe helpers. It does not give access, and it does not show that this work belongs on an Alliance cluster. I don't know the target cluster, the account or allocation, how fMRIPrep is provided (module, pinned `.sif`, or a wrapper), or the storage layout. I haven't observed any of these.
- This machine is not assumed to be the target.

**Smallest blocker:** there is no frozen plan and no confirmed target site. After those, the next blocker is an authorized connection to probe the site.

**What I need (up to three answers)**
1. Where is the plan (its path, or `plan.json`)? If there isn't one yet, give me the BIDS dataset path and I'll draft a plan first.
2. What is the target system? For an Alliance cluster, name it (Trillium, Nibi, Fir, Rorqual or Narval) and the account (`def-...`/`rrg-...`).
3. Am I allowed to run read-only probes on that cluster's login node, and a small probe job through the queue? A probe is not a pilot and not a cohort submission.

**How the profile will be resolved once those are known.** If the target is Alliance, I'll use `alliance-hpc` as the provider. The plan stays unchanged throughout:
- **Site profile:** run `alliance-hpc`'s `scripts/probe.sh <workdir>` on the target login host to get the scheduler, account, partition and QOS, walltime and concurrency limits, and storage (project, scratch, node-local). Each field gets a provenance label: observed, documented (the 2026-09-21 baseline), inferred, or unknown.
- **Provisioning and runtime:** choose between the site module and a pinned Apptainer image. Check the module's entrypoint so a containerized module doesn't get wrapped in a second container. Record the image or installation identity.
- **Proof inside the real compute context** (a probe job, not a login-node check):
  - the actual fMRIPrep version and CLI, plus the CPU and memory the job gets
  - read access to the BIDS inputs (including symlink targets) and the FreeSurfer license
  - test writes to the output, work, log, tmp, HOME and cache directories
  - bind-path translation for every path argument
  - the TemplateFlow assets are materialized, because compute nodes are offline
  - `--notrack`
  - the output directory is not the BIDS directory and doesn't hold results from a different fMRIPrep version
- **Resources:** one participant per array task. `--nprocs`, `--omp-nthreads` and `--mem-mb` must fit the actual allocation. Tune them from pilot accounting rather than fixed numbers.
- **Output:** an `execution.json` tied to the plan's hash, and a rendered job script for you to review.
- **Submission:** exactly one actor submits and retries. Per your instruction, neither `alliance-hpc` nor I will submit.

A profile can't change the recipe (spaces, SDC or STC, surfaces, software version, or cohort) to fit the machine. If the site can't satisfy the plan, I'll report the limitation back to you.
