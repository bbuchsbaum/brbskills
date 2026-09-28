# Execution profile: not resolved yet (blocked, nothing submitted)

I can't give you a verified execution profile yet. I also didn't want to make one up.
Two things are missing:

1. **There's no frozen plan to bind to.** The case directory has no `plan.json`, and I have no
   BIDS location or selected runs. I also don't have the fMRIPrep version, image identity, recipe
   or required outputs. An execution record points to one plan's scientific ID
   (`execution.content.scientific_id`). With no plan, there is nothing to resolve against. I have
   not written a recipe of my own, and a site profile is not allowed to change the recipe.
2. **No target site profile is verified.** The Alliance skill (`alliance-hpc`) is installed and
   I used it for guidance. Having it installed doesn't give access or authorization, and it
   doesn't confirm any site facts. Its cluster values are a **documented 2026-09-21 baseline**
   and are only starting points. You haven't named a target cluster, account or allocation, and
   I have no authorized connection. I ran no probes on a login node or a compute node.

Nothing was submitted, probed, staged or installed. No fixtures were run, because nothing
could be run until the blockers above are cleared.

## What I can resolve now (evidence level shown)

| Execution dimension | Status | Source |
|---|---|---|
| Target site / cluster | **unknown**. You need to choose one: Trillium, Nibi, Fir, Rorqual or Narval | none observed |
| Scheduler | **documented**: Slurm on all five Alliance systems | alliance-hpc systems baseline |
| Provisioning (module / preinstalled / image) | **unknown** | needs checks on the target: `module spider`, `type -a`, and the module entrypoint |
| Runtime (Apptainer vs. native vs. module wrapper) | **unknown**. A module may already wrap a container, so it must not be wrapped a second time | needs checking on the target |
| CPU/memory shape | **documented baseline only**, see below | alliance-hpc systems baseline |
| Account / partition / QOS / walltime limits | **unknown**, and this blocks submission | needs live `sacctmgr` / `scontrol` |
| Network on compute nodes | **documented** as offline on Rorqual and Narval. Nibi/Fir egress was *reported*, not verified. The profile assumes no network either way: TemplateFlow, license and image are prestaged, and `--notrack` is set unless your policy says otherwise | alliance-hpc systems baseline |
| Storage (BIDS / output / work / HOME / cache) | **unknown**. Scratch is disposable, so publish validated outputs to durable storage | needs `probe.sh` plus write tests inside an allocation |
| Submission owner | **proposed**: exactly one actor (you or this session, once authorized). The Alliance guidance does not submit on its own | skill policy |

### Candidate resource shapes (documented, not verified; any of these changes only the execution record)

- **Trillium CPU**: allocates whole nodes. The starter recipe uses 192 CPUs and no `--mem`; you
  submit from `$SCRATCH`, and there are no local disks. For fMRIPrep this means packing M
  subjects per node, with M×P ≤ 192 and M × per-subject memory + headroom within the node's
  real memory. One subject per node wastes most of the node.
- **Nibi / Fir / Rorqual**: shared-node sizing with a baseline of 192 CPUs / 750 GB. Request
  `--cpus-per-task=P` and an explicit `--mem` for each subject task (one array element per
  subject). Rorqual compute nodes are offline.
- **Narval**: baseline of 64 CPUs / 249 GB, and compute nodes are offline. Don't carry over a
  request sized for 192 CPUs.

For every option, set per-subject P (`--nprocs`) and O (`--omp-nthreads`, O ≤ P). Start with a
conservative memory figure, then adjust it using measurements from the pilot. I'm not giving a
universal memory or walltime number, because one hasn't been measured.

## What I need from you (at most three items)

1. **The plan.** Either the path to an existing `plan.json` / project recipe, or the BIDS path so
   I can take an inventory and propose one.
2. **The target.** Which cluster, which account (e.g. `def-…`/`rrg-…`), and whether this session
   may connect to it to run read-only probes.
3. **Probe authorization.** Permission to run a small probe under that allocation. It checks the
   actual fMRIPrep version and image identity, bind/path translation, license readability,
   materialized TemplateFlow assets, and writable work/output/HOME. Submitting a pilot or the
   full cohort is a separate authorization that you haven't given, and I'm not assuming it.

## Once those are supplied, I will

1. Run `alliance-hpc/scripts/probe.sh /absolute/workdir` on the target login host, then inspect
   the selected partition, account and QOS only.
2. Fill in `execution.json`: target, provisioning, runtime, scheduler, resources, path mappings,
   argv/env kept separate, and the asset manifest. Record each field as observed, documented,
   inferred or unknown. Then fingerprint it against the plan's ID with `records.py`.
3. Render the job script and run `bash -n` and `sbatch --test-only` on it, then stop before
   submitting.

Partial state kept: this draft profile. Smallest blocker: **the plan identity and the target
cluster/account.**
