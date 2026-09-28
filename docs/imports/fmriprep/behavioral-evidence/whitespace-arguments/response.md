# Result: whitespace arguments

Rendered a fixture-only batch payload that delegates to a Python argv-array
payload. The synthetic scheduler accepted the rendered script and returned
`SYNTHETIC-123`; its observer record is in `submissions.jsonl`. I then ran the
fixture batch payload locally, which invoked only `fake_runtime.py`. The captured
argv preserves `/config/filter $literal; name.json` as one literal argument and
captures `TEMPLATEFLOW_HOME=/templateflow` and `OMP_NUM_THREADS=2`.

The synthetic scheduler does not execute submitted scripts. The direct local
fixture invocation is therefore the argv-preservation demonstration, not a
claim of batch execution or fMRIPrep qualification.
