# Allocation check: this pack is oversubscribed

**Observed (from your context):** B = 6 subjects per task, M = 2 run concurrently, P = 8 `nprocs` per subject. The task has 8 CPUs.

**Check:** the pack needs at least M × P = 2 × 8 = **16 CPU slots**, and it has 8. That is 2× oversubscription. Also check that M ≤ B (2 ≤ 6, which passes) and that each subject's `--omp-nthreads` O is no more than its `--nprocs` P. Do not multiply P by O again: O is a per-process cap inside the P budget, not extra CPUs.

## Proposed correction (8 CPUs, no change to the recipe)

Both options satisfy M × P ≤ 8. Neither changes the recipe, the cohort, or B.

| Option | M | P (`--nprocs`) | O (`--omp-nthreads`) | CPU need | Subject waves per task | Memory need |
|---|---|---|---|---|---|---|
| **A (recommended default)** | 1 | 8 | ≤ 8 | 8 | 6 in sequence | 1 × subject-mem + H |
| B | 2 | 4 | ≤ 4 | 8 | 3 | 2 × subject-mem + H |

- **Option A** keeps each subject's `nprocs=8` as it is now and just runs subjects one at a time. I recommend it because you haven't given me the per-subject memory figure. It is the only option whose memory need does not double.
- **Option B** usually gives better throughput, because fMRIPrep does not scale linearly with threads. Use it only if pilot accounting (peak RSS from the scheduler, not `/proc/meminfo` on a login node) shows that 2 × subject peak memory + headroom H fits the task's memory allocation.
- **Wall time:** A runs 6 subjects back to back, and B runs 3 waves of 2 slower subjects. Before either goes to the full cohort, check the task time limit against the per-subject runtime from pilot accounting. If a limit is exceeded, reduce B (more tasks with fewer subjects each) rather than going back to 16 CPUs.

## What changes, and what does not

- These changes affect execution only. Record them as a new execution revision: M, P, O and the memory request. The scientific recipe (inputs, spaces, SDC/STC, software version, outputs) stays the same, and no subjects are dropped to make the pack fit.
- Update the rendered payload so every concurrent subject gets `--nprocs P --omp-nthreads O` explicitly. Then confirm the scheduler request still says 8 CPUs and memory ≥ M × subject-mem + H.
- Keep separate work and writable HOME directories for each concurrent subject. Make sure no two concurrent subjects write the same anatomy, work or output paths.
- If jobs already ran under the oversubscribed pack, check the accounting for OOM or time-limit failures before any retry. Resume only after confirming no live writer remains. Don't clear FreeSurfer `IsRunning` locks blindly.

## Still needed from you

1. **Per-subject peak memory** and the task's **memory limit**: these decide between A and B.
2. **Task wall-time limit**, together with pilot runtime per subject.

Until you tell me otherwise, I'll use Option A (M=1, P=8, O=8). Nothing has been submitted.
