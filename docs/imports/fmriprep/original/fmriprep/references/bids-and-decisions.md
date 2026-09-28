# Discovery, decisions, preferences

## Facts before questions

Use PyBIDS or an established BIDS-aware tool available on the authorized system.
A recursive sidecar glob is not an inheritance resolver. Inventory at the dataset,
subject, session, acquisition, run, and echo levels. Keep raw and derivative
namespaces separate. Preserve leading zeroes in subject labels. Exclude raw
`sourcedata/` and derivative trees from input discovery. Reconcile participants.tsv
with directories; neither alone proves that eligible images exist. [S7, S8, R2]

Make a compact run table. Record image entities and dimensions, voxel spacing,
TR/volume timing, number of volumes, available T1w/T2w/FLAIR/SBRef, echo grouping,
metadata provenance, and anomalies. Do not infer suitability for standard adult
processing solely from a dataset name. Missing population context only becomes a
question when it affects the recipe.

Resolve SliceTiming and SliceEncodingDirection. Inspect PhaseEncodingDirection,
TotalReadoutTime or supported source metadata, fieldmap type, and
B0FieldIdentifier/B0FieldSource or IntendedFor associations. Report correction
coverage per BOLD group. File names such as AP/PA are insufficient evidence of
axis/polarity or a valid association. Do not invent missing readout timing from a
scanner brand. Legitimate derivations must cite source fields and the applicable
formula. Store proposed metadata repairs separately. [S8]

Validate locally, using a compatible validator. Save tool/version, scope, errors,
warnings, and snapshot identity. A cached result is reusable only while the
relevant inputs and metadata are unchanged. Indexing with `validate=False` is not
validation. A pre-existing PyBIDS database must match the dataset and the paths
seen by the consuming process. [S1, S6]

## One recipe, not a survey

For ordinary adult volumetric fMRI, offer a single coherent starting recipe:
explicit T1w and one study-appropriate standard-space output; valid acquired
fieldmaps when available; data-driven slice timing and nonsteady-state handling;
full-quality processing; reports and confounds. For an otherwise unconstrained
adult study, `MNI152NLin2009cAsym:res-2` is a reasonable *proposal*, not a learned
user preference. Verify the actual grid. [S1–S5]

Explicitly resolve surface reconstruction. A volumetric output request alone does
not settle whether FreeSurfer should run: it can affect other preprocessing
steps. Retain the established project choice; otherwise explain the cost/benefit
briefly and state the proposed setting. Do not import a no-FreeSurfer preference
from a different fast-preprocessing project. [S4]

Do not interview about motion24, high-pass basis functions, smoothing, or the
first-level model here. These are downstream decisions. Record relevant downstream
intent only when it determines preprocessing outputs. [S5]

## Material decision triggers

| Observation | Action |
|---|---|
| Valid metadata, routine acquisition, established recipe | Show the effective recipe; no extra scientific questions. |
| Missing/ambiguous fieldmap coverage | Show affected runs; seek documented metadata or an approved no-SDC/SyN policy. |
| Multiple sessions/anatomicals | Determine whether the anatomical-reference choice needs study-level approval. |
| Existing outputs or FreeSurfer reconstructions | Inspect provenance/completeness before proposing reuse. |
| Surface/CIFTI or individual-echo request | Load the corresponding semantic section and check output dependencies. |
| Narrow FOV, lesions, pediatric/nonhuman, unusual acquisition | Do not claim the routine recipe is validated; investigate a tailored pilot. |
| Machine/resource destination unknown | Inspect available execution evidence; ask only unresolved authorization/site questions. |

An illustrative briefing, not a finding about the user's dataset:

> I propose T1w plus MNI152NLin2009cAsym on its 2-mm grid, the project's existing
> FreeSurfer setting, available acquired-fieldmap correction, and slice timing
> where supported. Two runs lack a resolved fieldmap association; they are held
> out pending a metadata fix or your approval of a different SDC policy. I will
> test one representative subject before the cohort. Any changes to the recipe?

Do not treat silence as launch approval. If the user already authorized a bounded
launch with applicable defaults, do not ask again without a material change.

## Preference storage

Use project-local `.fmriprep-agent/preferences.json` and, optionally, a user file
under the user's configuration directory. Keep them separate from the launcher's
INI. Shared skill files contain policy; they are not mutable personal memory.
Suggested rule fields: key, value, scope/conditions, explicit provenance,
confirmed_at, and supersedes. The example asset is intentionally unconfirmed.

Distinguish three stores: scientific preferences; site execution profiles; run
observations. A prior failure is evidence, not a preference. A one-run template
change is not a universal default. Cache deterministic observations with input
fingerprints; no consent is needed to record authorized run provenance. Reusable
personal preferences require the user's explicit save instruction/confirmation.

A locked project recipe does not silently yield to a new user default. If the
current request conflicts with it, show the consequence and create an approved
revision. Before reuse, check both rule scope and compatibility.
