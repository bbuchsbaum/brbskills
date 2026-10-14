# MeterSummary — local pilot

The pilot user runs `python3 main.py readings.json` and receives a JSON object
containing the count and arithmetic mean of the numbers in that file. A missing
or invalid input must fail clearly with a nonzero exit. Supported inputs are
nonempty JSON arrays of finite numbers. No network or third-party packages are
needed. Run component checks with `python3 -m unittest discover -s checks -v`.

See decisions.md for accepted scope. The old roadmap is historical context.
