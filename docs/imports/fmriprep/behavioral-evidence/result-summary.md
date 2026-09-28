# fMRIPrep synthetic behavior results

Artifact root: `/private/tmp/fmriprep-behavior-0lLiWc`

## Cases

| Case | Outcome | Primary evidence |
| --- | --- | --- |
| wrapper-absent | Direct synthetic payload completed; argv and required env preserved. | `wrapper-absent/capture.jsonl` |
| whitespace-arguments | Synthetic submission observed; local fixture batch payload completed with literal whitespace argument preserved. | `whitespace-arguments/submissions.jsonl`, `whitespace-arguments/capture.jsonl` |
| duplicate-subject | Retry blocked; earlier attempt remains `UNKNOWN`. No submit performed. | `duplicate-subject/state.json`, `duplicate-subject/tool-evidence.md` |
| metadata-inheritance | Effective `SliceTiming` values explained from supplied hierarchy; no validation claimed. | `metadata-inheritance/response.md` |

## References read

- `skills/fmriprep/SKILL.md`
- `skills/fmriprep/references/execution.md`
- `skills/fmriprep/references/records.md`
- `skills/fmriprep/references/bids-and-decisions.md`
- The four requested entries only from `skills/fmriprep/tests/fixtures/cases.json`
- Permitted fixture implementations: `fake_runtime.py` and `fake_scheduler.py`

No question was required. There is one operational blocker: the duplicate-subject
case requires real queue/accounting and live-writer reconciliation before retry;
the supplied synthetic state cannot resolve it.
