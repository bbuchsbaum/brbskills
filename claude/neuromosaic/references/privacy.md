# Report privacy and interpretation

Decide the disclosure class before rendering: static aggregate images; interactive
group voxels; subject-linked data; or shareable/public artifact. Separate the
permission to generate locally from permission to upload, email or publish.
An offline HTML report can embed full image arrays or participant-linked data.
No CDN/network request does not imply anonymity. The package's documented
interactive modes explicitly expose recoverable voxel values.

Keep direct identifiers, reidentification keys, free text, dates and individual
covariate rows out of public reports by default. Group maps can still be sensitive
in small or special cohorts. Do not infer consent from BIDS conformance or from a
pseudonymous subject label. Follow the user's approved institutional/data boundary.
Do not send real reports as skill eval fixtures; use synthetic data.

Interactive threshold/palette controls are exploratory. Label the fixed inferential
result, family/alpha and any display-only threshold separately. Changing a view
must not rewrite the analysis receipt or imply a new corrected finding. Preserve
a readable static fallback with the authoritative settings. Do not tune scientific
thresholds to make the report visually satisfying.

When parcel/cluster plots use data selected by the same statistic, state that
selection explicitly and treat them as descriptive. For independent confirmation
use independent regions/data or a suitable validated selection-aware method.
Atlas overlap supplies anatomical annotation, not evidence of a psychological
mechanism. Report empty/negative results and uncertain map meaning honestly.

Before sharing, inspect HTML/QMD/RDS/asset directories for embedded data and the
actual paths/values they contain. Sharing only the HTML of a bundled report can
break it; sharing its entire directory can disclose more than expected. List the
required files and their disclosure level in the handoff.
