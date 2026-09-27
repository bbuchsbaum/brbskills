# Local helper commands and exact limits

`workbench.py` uses Python 3.10+ standard library only. It never runs R, evaluates
arbitrary Python/R strings, calls a model/network API, submits jobs or publishes.
The scripts are optional state aids; a narrow API question need not create state.

```sh
W=skills/fmri/scripts/workbench.py
python3 "$W" init /work/plan.json --analysis-id face-scene --scope first_level group report
python3 "$W" validate /work/plan.json --stage first_level --purpose pilot
```

The new plan intentionally fails readiness checks. The agent edits it only from
reviewed evidence and saves native R code separately. Empty configs, unconfirmed
material decisions, failed/missing required checks, unresolved model-visible data
policy and missing compute budgets prevent approval. Full first-level/group
approval additionally requires a documented pilot. The schema defines document
shape; `validate` adds admission checks, not statistical proof or a JSON-to-R compiler.

```sh
# Fingerprint reviewed files. Add every actual input/dependency to be checked.
python3 "$W" seal /work/plan.json \
  --file inputs=/work/selected-input-index.json \
  --file code=/work/analysis.R --file environment=/work/renv.lock \
  --file input.bold01=/data/sub-01_preproc_bold.nii.gz
python3 "$W" digest /work/plan.json
```

`seal` hashes exactly the named files and clears approvals. It does not recursively
hash paths referenced inside a JSON/R file. The input index should contain its
own content hashes, and a separately reviewed verifier must check all actual
members, or seal them individually. This avoids pretending a changed BOLD image
is detected merely by hashing an unchanged text index. Full imaging checksums may
be costly; initial discovery can be cheap, but use a documented integrity strategy
before full execution and resume. Paths in fingerprint records are local absolute
paths; relocation requires rebinding and review.

After actual user approval, record the exact digest and its evidence:

```sh
python3 "$W" approve /work/plan.json --stage first_level --purpose pilot \
  --digest THE_REVIEWED_DIGEST --confirmed-by-user --evidence 'Reference to actual approval'
python3 "$W" check /work/plan.json --stage first_level --purpose pilot
```

The boolean is not a request to fabricate approval. A successful check means the
recorded gate and sealed files match; it cannot prove user identity, institutional
compliance or scientific calibration. The helper does not launch work after a
successful check. It also does not automatically write full job receipts or keep
HPC sessions alive. Those are host/agent/native job responsibilities.

## Preference API

```sh
python3 "$W" prefs list --file /work/.fmri/preferences.json
# Only after the user explicitly asks to remember this scoped preference:
python3 "$W" prefs set --file /work/.fmri/preferences.json \
  --key first_level.confounds --value-json '"motion24"' \
  --when-json '{"analysis":"task_glm","pipeline":"fmriprep"}' \
  --confirmed-by-user --evidence 'Reference to actual preference consent'
python3 "$W" prefs resolve --project /work/.fmri/preferences.json \
  --context-json '{"analysis":"task_glm","pipeline":"fmriprep"}'
```

`resolve` can also read `--user`, `--current`, and `--locked` JSON files. Current
and locked files are simple key→value objects supplied from reviewed analysis
state. It reports provenance and conflicts. No formula/command string is executed.
`prefs remove` takes the same key/when/consent arguments; it removes the matching
active rule. Equal-specificity conflicts are conservatively reported even when a
higher layer would otherwise replace a value; explicitly reconcile them.

Writes use an exclusive sidecar lock and atomic replacement. Existing locks are
not silently deleted as stale. This is cooperative local protection, not a
distributed lock or protection against a hostile process with write access.
An interrupted installer may leave earlier selected skills installed; it never
overwrites them, and its output/error identifies failure. Inspect before retrying.
