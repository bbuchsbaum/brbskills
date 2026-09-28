# Records and identities

Use these records when preparing execution or preserving a resumable handoff.
For an explanation, use prose. For an existing project, map its established state
to this contract instead of creating a competing tracker. JSON examples are
editable illustrations, not rriscripts INI, fMRIPrep config, or launchable jobs.

## Contents

- [Content](#content-and-observations)
- [Fingerprinting](#fingerprinting-convention)
- [Authority and revision](#authority-and-revision)
- [Submission and recovery](#submission-and-recovery)

## Content and observations

`plan.json` and `execution.json` have `schema_version: 1`, `kind`, `content`,
`content_id`, and `example_only`. Everything defining the run belongs in
`content`. Evidence, decisions, approval records, timestamps and evolving status
live outside it. Unresolved values may be null in a draft; do not silently fill
unknown facts with defaults. Set `example_only: false` only for a real record.

| Record | Required content before the relevant execution stage |
|---|---|
| plan | inputs and selection; software identity; scientific recipe; required outputs |
| execution | scientific_id; target; provisioning; runtime; scheduler; resources; paths; payload; scripts; assets; network; storage |
| receipt | attempt_id; scientific_id/execution_id; durable submission intent; exact script identity; process, outputs, QC and publication states |

For `inputs`, identify the selected runs and effective inherited metadata, original
snapshot and validation scope/version/result. Separate data identity from its
current mount location. Reuse content digests or trustworthy immutable dataset
versions; state limitations if only size/mtime inventories are available. An
inventory fingerprint is not proof that image bytes are unchanged. Validation
warnings need disposition, not automatic dismissal.

The recipe includes explicit templates and verified grids, reconstruction and
anatomical reference, per-branch SDC/STC policies, nonsteady-state handling,
requested echoes/surfaces, quality and other nondefault method choices. Pin
fMRIPrep and the actual image or installation identity. A native installation
without an immutable environment must declare that limit; do not fabricate a
container digest. Required outputs must enumerate selected runs and products.

An execution records actual setup commands, executable identity, mapped paths,
argv, allowlisted environment, cwd, rendered `scripts` references, allocation,
concurrency, retained work,
asset manifest and publication procedure. Store seed/thread settings here unless
the study treats them as fixed science; always retain their values. Methods must
remain unchanged across providers even when runtime and path syntax differ.

## Fingerprinting convention

The bundled [records.py](../scripts/records.py) hashes the UTF-8 encoding of
`{"schema_version":1,"kind":...,"content":...}` with SHA-256. Its JSON encoding is
Python `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False,
allow_nan=False)`, without a newline. Prefix the hexadecimal result with
`sha256:`. This is the skill's v1 encoding, not a claim of RFC 8785 compatibility.
Keep numeric representations stable (1 and 1.0 differ); key order and input
whitespace do not matter. Duplicate JSON keys and nonfinite numbers are rejected.

The identity excludes `content_id`, evidence, approval and status; there is no
self-hash cycle. Content references to small manifests/scripts/configs use
`{"$file":"relative/path","sha256":"sha256:<64 lowercase hex digits>"}`.
Resolve them relative to one explicit artifact root, never the current shell
implicitly. The checker verifies file bytes and rejects traversal or symlinks
escaping that root. Do not use `$file` for private license contents; record a
protected local locator and visibility evidence instead. A referenced manifest's
hash binds its bytes, not every data file it describes: verify those data identities
separately. Keep artifacts outside raw BIDS and use atomic replacement when
persisting revisions.

```bash
python /path/to/skill/scripts/records.py fingerprint plan.json
python /path/to/skill/scripts/records.py fingerprint execution.json
python /path/to/skill/scripts/records.py check plan.json execution.json \
  --artifact-root /absolute/campaign --scope pilot --receipt receipt.json
```

Record the returned identity in `content_id`. Put the plan identity in
`execution.content.scientific_id`, then fingerprint execution. The helper never
edits files, submits, or contacts a service. It exits 0 on success and 2 with a
one-line reason on any rejection, including malformed, non-UTF-8, deeply nested or
oversized (>16 MiB, enforced by a bounded read, so FIFOs and devices are capped
too) JSON and symlink loops; a leading UTF-8 BOM is accepted.

`check` requires nonexample records, major content fields, no null/blank content,
matching IDs, referenced file hashes, and an applicable recorded authorization.
Inside `payload.argv` and `payload.env` an empty string is a literal value (for
example an intentionally empty variable); only null is unresolved there. For each
supplied receipt it also requires:

- a unique `attempt_id` and a unique target/owner/token submission tuple. These
  identity values and `job_id` are compared exactly, so surrounding whitespace is
  rejected rather than silently normalized;
- `submission.state` in `prepared`, `not_submitted`, `unknown`, `submitted` or
  `terminal`. `prepared`/`not_submitted` must not carry a `job_id`;
  `submitted`/`terminal` must; `unknown` may carry a captured one. A `job_id`
  may appear only once per target among the supplied receipts;
- `process.status`; `outputs`, `qc` and `publication` may be absent or null, but
  when present each needs a `status`. The helper checks presence, not meaning;
- a `script` whose normalized `$file` path and `sha256` match a `scripts` entry in
  execution content (annotation keys are ignored). Changing its bytes requires a
  new execution ID.

It does **not** validate fMRIPrep semantics, full field schemas, permission,
resource sufficiency, scheduler state or pilot/QC evidence. A successful check
explicitly leaves readiness and consent authenticity unassessed.

## Authority and revision

A plan's `authorizations` records the scientific ID, scopes (`prepare`, `probe`,
`pilot`, `cohort`, `publish`, `cleanup`), recorded_at, source (the actual user
instruction or approved protocol reference), and limits. Include target,
participants, resources/concurrency, retry budget and destination as applicable.
Never infer approval from a boolean or from an agent-created record. Check those
limits against the execution content manually; the helper only checks the binding
and presence of provenance. Existing authorization can cover several stages.

A scientific edit changes the plan ID and invalidates old approvals unless the
existing instruction explicitly covers that change; record that provenance anew.
An infrastructure edit changes execution ID and requires checking the authorized
bounds, affected compute proof and pilot applicability. Observation/QC updates do
not rewrite scientific content. Preserve prior revisions, not just the latest JSON.
A pilot can select a subset of the frozen cohort via execution content; the receipt
must identify that subset and the covered acquisition branches.

## Submission and recovery

Before invoking a submit command, persist attempt ID, unique submission token,
target cluster/scheduler, owner, intent time, plan/execution IDs and exact script
reference. Capture returned job ID and acknowledgment. If interrupted during the
submit call, treat a prepared intent as potentially submitted; reconcile even if
no job ID was recorded. `unknown` blocks resubmission until queue/accounting and
ownership evidence resolve it. A token aids lookup but does not promise exactly
once semantics. Local execution needs equivalent PID/start-time/host evidence.

Receipts are per attempt. Keep original submission argv/env/script, allocation,
actual version, selected units, timestamps, logs and observed processing. New
execution revisions receive new receipts. The checker detects duplicate attempt
IDs, repeated target/owner/submission-token tuples and repeated target/job IDs
among supplied receipts, not duplicate jobs across a cluster.
Reconcile all live writers before retry, even if a new attempt ID is available.
Never concatenate old successful outputs into a new receipt without compatibility
and provenance checks. Preserve per-run failed/missing/QC-held states.

See [operations](operations.md) for pilot coverage, QC and durable publication.
