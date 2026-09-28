I won't cat the license into the job log. The license key is a credential, and job logs get copied, shared and archived. Its contents also can't answer your question: "license file not found" means fMRIPrep couldn't see the file inside the job/container, not that the file was wrong. I'm also not resubmitting yet, because nothing about the job has changed and it would fail the same way.

**Likely cause.** `FS_LICENSE` works on the login node, but that doesn't reach the container. With `apptainer run --cleanenv`, host environment variables like `FS_LICENSE` are dropped. Even without `--cleanenv`, a host path is only visible inside the container if it is bind-mounted. We don't know the job's binds, so that's the first thing to check.

**Fix (the preprocessing settings stay the same; only the execution setup changes):**

1. Pass the license path explicitly with a read-only bind and the flag, not the environment variable:
   ```
   apptainer run --cleanenv \
     -B "$FS_LICENSE":/opt/freesurfer/license.txt:ro \
     ... <fmriprep.sif> /data /out participant ... \
     --fs-license-file /opt/freesurfer/license.txt ...
   ```
   Also check that the host path is on a filesystem the compute nodes mount. Some `$HOME` or `/tmp` paths on login nodes aren't visible from compute nodes.

2. To check whether it's the right license without exposing it, add a short preflight to the job script before fMRIPrep starts. It prints only whether the file is readable, its size and a hash:
   ```
   apptainer exec --cleanenv -B "$FS_LICENSE":/opt/freesurfer/license.txt:ro <fmriprep.sif> \
     sh -c 'test -r /opt/freesurfer/license.txt && echo LICENSE_READABLE; wc -c < /opt/freesurfer/license.txt; sha256sum /opt/freesurfer/license.txt | cut -d" " -f1'
   ```
   On the login node, run `sha256sum "$FS_LICENSE"` and compare. If the hashes match, the job sees the same file you checked. If the preflight fails, the bind or path is the problem. Please also check that the job log doesn't already contain the license text from an earlier debugging attempt. If it does, trim or restrict access to that log.

3. Before resubmitting, confirm the failed job has finished and that no other attempt is writing to the same subject's output or work directory. Then resubmit with the fixed binds. If you'd rather not spend a full job on it, first run the preflight as a short job.

**Blocker:** I need the job script (or launcher configuration) to see the actual binds and whether `--cleanenv` or `--fs-license-file` is set. Send it and I'll patch those lines and resubmit once the preflight passes.
