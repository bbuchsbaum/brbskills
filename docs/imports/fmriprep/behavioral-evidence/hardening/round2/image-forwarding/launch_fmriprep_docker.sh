#!/usr/bin/env bash
# Direct raw-Docker fallback for the rriscripts fmriprep-docker route.
# NOT RUN. Fill every <...> from `fmriprep_launcher.py probe` (Effective config
# values) and the approved plan; nothing here is verified on the target host.
set -euo pipefail

IMAGE='<configured image>@sha256:<digest>'   # docker image inspect --format '{{index .RepoDigests 0}}' <image>
SUB='<01>'                                   # one participant per invocation
BIDS='<abs bids dir>'
OUT='<abs output dir>'                       # not equal to / inside BIDS
WORK='<abs work root>'/sub-"$SUB"
TF='<abs materialized TemplateFlow cache>'
LICENSE='<abs fs license file>'

docker_args=(
  run --rm
  -u "$(id -u):$(id -g)"
  -v "$BIDS":/data:ro
  -v "$OUT":/out
  -v "$WORK":/work
  -v "$TF":/templateflow
  -v "$LICENSE":/opt/freesurfer/license.txt:ro
  -e TEMPLATEFLOW_HOME=/templateflow
  -e HOME=/work/.home
  "$IMAGE"
)

# Application argv: copy exactly what the launcher's effective config would emit.
app_args=(
  /data /out participant
  --participant-label "$SUB"
  -w /work
  --fs-license-file /opt/freesurfer/license.txt
  --output-spaces '<SPACE_1>' '<SPACE_2>'
  --nprocs '<P>' --omp-nthreads '<O>' --mem-mb '<MB>'
  --notrack
  # <--fs-no-reconall ONLY if the plan says so; launcher adds it unless fs_reconall=true>
  # <--skip-bids-validation ONLY with a matching validator record>
  # <--cifti-output 91k|170k if the plan requires CIFTI>
  # <extra options from config, as separate tokens>
)

mkdir -p "$WORK/.home"
docker "${docker_args[@]}" "${app_args[@]}"
