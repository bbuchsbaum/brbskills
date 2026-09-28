# Effective launcher configuration review: pilot is blocked

**Verdict:** Don't generate the pilot yet. Your explicit INI sets only the image, so it is an overlay on top of the other files. The launcher also loads the system, user and project INIs, and two inherited settings contradict the approved plan.

## What the launcher will actually use

| Setting | Where it comes from | Effective value | Approved plan | Status |
|---|---|---|---|---|
| Image | Explicit INI | The image you set | The pinned image | Fine only if the route actually uses it (see below) |
| BIDS validation | Project INI | **Skipped** | No validation receipt exists | **Conflict: blocks the pilot** |
| Surface reconstruction | User INI | **Disabled** | Reconstruction is required | **Conflict: blocks the pilot** |
| Everything else (spaces, grids, anatomical reference, resources) | System, user or project INI, or launcher defaults | Not yet inspected | Must match the plan | Unverified |

What I haven't seen: the installed launcher, its revision, the system INI and the exact precedence order. I don't know which layer wins, so I'm not assuming it. The effective arguments have to come from the installed launcher's own output.

## Why each conflict blocks the pilot

1. **Reconstruction is disabled by the user INI.** That file is a personal preference, and it would silently remove surface reconstruction from the approved recipe. A pilot run with it would test a different recipe, so it wouldn't qualify the approved one. Surfaces can't be dropped without a revised, approved plan.
2. **The project INI skips validation, and there is no receipt.** Validation can only be skipped when there is a validator record for this exact input snapshot. Without one, validation has to run, or you have to run the validator first and record its version, scope and result, including how each warning was handled.

## How to fix it without touching anyone's files

Leave the user and project INIs as they are. Instead, add explicit overrides to the INI you pass for this run, next to the image:

- Turn reconstruction on explicitly. Don't just delete the user-level setting and rely on defaults.
- Turn validation on explicitly. Only set it to skip once there is a validation receipt that matches this input.
- State the plan's output spaces, grids and other nondefault settings explicitly too, so no example-file or inherited default fills them in.

Get the exact INI key names from the installed launcher's `--help` or its source. I haven't guessed them.

## Checks to run before the pilot

```bash
fmriprep_launcher.py --help          # record install path and revision; confirm INI keys and layering order
fmriprep_launcher.py probe
fmriprep_launcher.py print-cmd ...   # with the same explicit INI you will use for the pilot
```

In the `print-cmd` output, check that:

- there is no `--fs-no-reconall` and no `--skip-bids-validation`;
- the output spaces, grids and anatomical reference match the plan;
- the image in the output is the pinned one. On the `fmriprep-docker` route this launcher revision doesn't pass the image explicitly, so a `container=` setting doesn't prove which image runs. If that's your route, use one that passes the image or bypass the launcher;
- the environment variables (`APPTAINERENV_*`/`SINGULARITYENV_*` prefixes) are listed separately from the command arguments, and every path argument has been checked as it appears inside the container.

Save the effective settings and the `print-cmd` output with the execution record. When the command matches the plan, generate the pilot bundle with `slurm-array --script-outdir "$JOB_DIR"` and inspect it before submitting. Submission is a separate step that needs its own authorization.

**Fallback:** if the installed launcher can't produce the approved settings, send the same fMRIPrep arguments through a direct runtime command or a minimal scheduler script instead. Neither route may change the recipe.
