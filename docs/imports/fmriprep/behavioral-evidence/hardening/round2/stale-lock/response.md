I haven't deleted the lock or resubmitted yet. Yesterday's sub-07 array task might still be queued or running, and nobody has checked. If it is and I clear `IsRunning.lh+rh` and start a new run, two recon-all processes will write to the same FreeSurfer subject and corrupt the anatomy. That lock is doing its job until we show nothing else is running.

**What has to be true first** (all three):
1. The scheduler shows no pending or running job for sub-07. Check yesterday's array, including the sub-07 task specifically:
   ```
   squeue -u $USER -o "%i %j %T %N %R"          # anything still queued or running?
   sacct -j <ARRAY_JOBID> --format=JobID,JobName,State,ExitCode,NodeList,Start,End
   ```
2. Read the marker (don't delete it):
   ```
   cat <output>/sourcedata/freesurfer/sub-07/scripts/IsRunning.lh+rh
   ```
   It records HOST, PROCESSID, USER and DATE. If HOST is a compute node, a login node can't see its processes, so the scheduler check decides. If HOST is reachable, confirm PROCESSID isn't a live recon-all. (If you use fMRIPrep ≥25.2 with session tracking, the FreeSurfer subject directory may have a session suffix.)
3. No other session, recipe or array task is aimed at this FreeSurfer subject.

**What happens next depends on the answer:**
- **The sub-07 task is PENDING or RUNNING:** leave the lock alone and don't resubmit. Let that task run, or `scancel` it and wait for it to leave the queue, then clear the lock and rerun.
- **Nothing is live** (for example, sacct shows the old task as FAILED, CANCELLED, TIMEOUT or NODE_FAIL): the lock is stale. I'll remove only that subject's markers:
  ```
  rm <output>/sourcedata/freesurfer/sub-07/scripts/IsRunning.*
  ```
  No globbing across subjects, and I won't touch the subject directory. I'll record the marker contents, the time and the sacct evidence in the attempt record. Then I'll resubmit sub-07 alone with the same recipe (same fMRIPrep image and options, same output and work dirs) so the FreeSurfer and work-dir progress already made gets reused.
- **The state is unclear** (the array ID is lost, or sacct shows nothing): treat it as UNKNOWN and reconcile by job name and output markers before any new submission.

Send me the `squeue`/`sacct` output and the marker contents, or tell me where the array job ID was recorded, and I'll finish this: clear the lock and submit sub-07 once it's clear, or hold if it isn't.
