# Validation

[Offline tests](test_publish_private.py) run the script against an in-memory fake of the here.now endpoints it
uses: password is set before any content upload, hidden paths are skipped, unchanged reruns are no-ops, changed
files create a new version, live drift and missing password protection are refused, a hosted hash mismatch fails,
and `index.html` is required. They do not contact here.now.

Live use (2026-11-09, one site): a group-only report with three self-contained neuromosaic pages (8 files,
~140 MB) published, verified by owner-API hash readback, and returned 401 on all unauthenticated probes. That run
found the hidden-path problem (an agent hook wrote a session log into the site directory), which the script now
excludes. The vendor API contract can change; trust live API behavior over this record.
