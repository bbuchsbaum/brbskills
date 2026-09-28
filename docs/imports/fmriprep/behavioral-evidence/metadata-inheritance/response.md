# Result: metadata inheritance

| Run | Effective SliceTiming | Provenance |
| --- | --- | --- |
| `sub-01/ses-01/func/sub-01_ses-01_task-rest_run-1_bold.nii.gz` | `[0.0, 1.0]` | Inherited from dataset-level `task-rest_bold.json`. |
| `sub-01/ses-02/func/sub-01_ses-02_task-rest_run-1_bold.nii.gz` | `[1.0, 0.0]` | More-specific `sub-01/ses-02/sub-01_ses-02_task-rest_bold.json` overrides the dataset-level value. |

The dataset-level `RepetitionTime: 2.0` remains inherited for both runs because
the session sidecar supplies only `SliceTiming`. This is metadata-hierarchy
reasoning from the supplied fixture; no image headers or BIDS validation were
available or run.
