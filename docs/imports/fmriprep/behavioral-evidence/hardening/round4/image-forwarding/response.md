# Pinned fMRIPrep launch with the configured image

## Short answer: the wrapper route can't pin your image

With rriscripts' fmriprep-docker backend, your configured `container=` image is **not used**. The launcher never passes `--image`/`-i` to `fmriprep-docker`. The wrapper therefore runs its own default, `nipreps/fmriprep:<wrapper version>`. The image is set by whichever wrapper version is installed, not by your config. Pinning `container=` in the INI changes nothing on this route. `print-cmd` or `slurm-array` would give you a launch that looks configured but runs a different image. I have not prepared one.

A second gap on the same route: the launcher sets `TEMPLATEFLOW_HOME` on the host. The 25.2.5 wrapper ignores it and mounts no cache, so your configured TemplateFlow cache is also not used. The container falls back to its built-in templates or the network.

(Reviewed launcher revision `db7a0aa`. Pre-fix installs (≤ `acb0a38`) have the same image gap, plus a bug where they pass `--env TEMPLATEFLOW_HOME=/path` as a single token, which breaks the wrapper's two-token `--env` parsing.)

## Before anything runs: confirm which install you have

The review covered the repository, not necessarily the copy on your target machine. On the machine that will run the job:

```bash
type -a fmriprep_launcher.py
sha256sum <libdir>/fmriprep_launcher.py <libdir>/fmriprep_backend.py <libdir>/fmriprep_shared.py
fmriprep_launcher.py --no-default-config --config <your.ini> probe   # save the output
```

`db7a0aa` hashes: launcher `ad10426d…97c4`, backend `72fb8bb5…258a163`, shared `ca1c2aad…6b5a`. If they differ, classify the era with the greps in the rriscripts reference before trusting any launcher output. The fallback below does not depend on the launcher revision.

## Fallback: same recipe, direct Docker payload

This passes the same logical arguments the launcher would, with the image pinned by **digest** and the TemplateFlow cache mounted explicitly. One subject per invocation:

```bash
IMAGE='<registry/repo>@sha256:<digest of the configured image>'   # resolve from the configured tag, record it

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -e TEMPLATEFLOW_HOME=/templateflow \
  -v <bids>:/data:ro \
  -v <out>:/out \
  -v <work>/sub-<label>:/work \
  -v <templateflow_cache>:/templateflow:ro \
  -v <fs_license>:/opt/freesurfer/license.txt:ro \
  "$IMAGE" \
  /data /out participant --participant-label <label> \
  -w /work --fs-license-file /opt/freesurfer/license.txt \
  <recipe options: --output-spaces …, reconall setting, other approved flags> \
  --nprocs <P> --omp-nthreads <O> --mem-mb <MB> --notrack
```

Carry these over from your launcher config and approved recipe. Set each one explicitly rather than inheriting a default:

- **Image:** resolve the configured tag to a digest once (`docker image inspect --format '{{index .RepoDigests 0}}' <tag>`), then launch by digest. Record the digest and the `--version` the image reports.
- **Recon-all:** the current launcher runs recon-all unless configured `false`. Match the approved recipe exactly: add `--fs-no-reconall` only if the recipe says so.
- **BIDS validation:** leave it on, unless a validator record matches this input.
- **CIFTI:** if the config had `cifti_output = true`, add `--cifti-output 91k` (or 170k if that is what the recipe specifies).
- **`extra`:** carry over each token from the config. Any file path among them (filters, configs, derivatives) needs its own `-v` mount and a container path.
- **Subjects:** use explicit labels from your inventory, not `all`.
- **Resources:** set `--nprocs` and `--mem-mb` per subject from the actual allocation, never from a login node's defaults.
- **Telemetry:** keep `--notrack`, as the launcher does.

Alternative that keeps the wrapper: call `fmriprep-docker` directly with `-i <image>`. Its `--env` takes **two** tokens (`--env TEMPLATEFLOW_HOME /templateflow`), and it creates no mount for that path. You would still need to confirm that the wrapper version accepts a digest reference and mounts the cache. Raw Docker is the cleaner of the two.

For a Slurm job, render this as the job's payload, keeping argv as an array: no `read -a`, no `eval`. Keep the environment map separate from the argv.

I checked the argv shape with the local synthetic recorder (`fake_runtime.py`). All tokens came through intact: the image stayed a single token after the runtime options, and `-e`/`-v` split as intended. That checks quoting only. It says nothing about readiness.

## Still open before a pilot

1. **Image digest.** Not known here. Resolve it on the execution host and record it.
2. **Compute-context proof,** run through the actual runtime:
   - Docker daemon access.
   - Mount visibility for the BIDS, output, work, license and TemplateFlow paths.
   - Output ownership.
   - Image architecture (important on Apple Silicon).
3. **TemplateFlow cache.** It must be fully materialized for the recipe's spaces, readable at `/templateflow`, and needing no writes. Otherwise mount it read-write, one writer at a time.
4. **Output namespace.** Use a fresh `<out>`, or one whose `dataset_description.json` records the same fMRIPrep version.
5. **Pilot.** Run one representative subject per acquisition branch, and review QC before releasing the cohort.

Nothing has been submitted. Submission is a separate, authorized step. If you send the configured image tag, the paths, and the recipe's space and reconall choices, I'll fill in the payload and give you the per-subject command or the rendered job script.
