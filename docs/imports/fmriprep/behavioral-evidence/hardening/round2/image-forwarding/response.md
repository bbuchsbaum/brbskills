**The wrapper can't make a pinned launch with your configured image, so I've prepared a direct Docker fallback instead.** Nothing was run or submitted.

**Why the wrapper won't work.** The rriscripts fmriprep-docker route ignores your `container=` setting. The direct command (`print-cmd`) and the Slurm batch script never pass `--image` to `fmriprep-docker`. The wrapper then falls back to `nipreps/fmriprep:<wrapper version>`, so the image you get depends on which wrapper is installed, not on your config. Both the `main` (`acb0a38`) and `fix/fmriprep-issues-3-5` (`747775e`) revisions have this problem, so updating the launcher won't fix it.

The direct route has a second defect: it adds `--env TEMPLATEFLOW_HOME=/path` as one token. The 25.2.x wrapper expects two (`--env NAME value`), so argument parsing fails whenever TemplateFlow binding is on, which is the default. Calling `fmriprep-docker --image ...` yourself would fix the image, but the wrapper's `--env` does not mount the TemplateFlow cache.

**Fallback: `launch_fmriprep_docker.sh`** (template, placeholders only). It calls raw `docker run` for one participant, with the command-line arguments kept in bash arrays and never passed through `eval`:
- The image is referenced by digest (`<image>@sha256:...`), taken from `docker image inspect --format '{{index .RepoDigests 0}}' <configured image>`.
- It sets explicit mounts: BIDS read-only, output, a work directory per subject, a filled TemplateFlow cache, and the license read-only. It also passes `-e TEMPLATEFLOW_HOME=/templateflow`, `-u UID:GID` and a writable HOME under work.
- `--notrack` is kept to match the launcher.

**To make it faithful to your config**, copy the fMRIPrep arguments from `fmriprep_launcher.py probe` ("Effective config values"), or from `job_manifest.json` `build_config` if a bundle already exists. Pay particular attention to the launcher defaults that change the science:
- **`fs_reconall`:** the launcher adds `--fs-no-reconall` unless this is set to `true`. Include that flag only if the approved recipe says so.
- **`skip_bids_validation`:** often `true` by default. Keep skipping only if there is a matching validator record.
- **`cifti_output`:** a `true` value means `91k`.
- **`nprocs`/`mem_mb`:** set them explicitly rather than taking the login node's values.
- **Subjects:** list them explicitly.
- **`extra` tokens:** carry each one over as a separate token.

Then compare the rendered fMRIPrep arguments against `print-cmd` and the plan.

**Still needed before launch:**
1. The digest of the configured image.
2. The saved `probe` output, listing the config files in load order and the effective values.
3. A check on the target host that you can reach the Docker daemon, the mounts are visible, the image architecture matches the host, and the TemplateFlow assets are filled in.
4. A one-subject pilot for each acquisition branch, with QC review, before running the full cohort.
