# Result: wrapper absent

Prepared a direct fixture-only payload without rriscripts. It invokes only the
permitted synthetic runtime with the supplied application argument vector held
as a Python list. The captured argv preserves `/config/filter $literal; name.json`
as one literal argument. The requested environment values were captured as
`TEMPLATEFLOW_HOME=/templateflow` and `OMP_NUM_THREADS=2`.

This is command-rendering evidence only. No Apptainer, Slurm, fMRIPrep, dataset,
or scientific qualification was invoked or established.
