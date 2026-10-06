# Cross-domain analyses

Use this route when source/target, encoding/retrieval, matched items, or adaptation
are part of the question. Match the scientific target before choosing a model.

| Question | Public route | Main distinction |
|---|---|---|
| Classify target trials by source prototypes without adaptation | `naive_xdec_model(dataset, design, link_by = ...)` | Direct correlation-based transfer baseline |
| Compare matched-item similarity, identification, or between-phase geometry | `era_rsa_design()` / `era_rsa_model()` | Similarity and geometry readouts, not an adapted classifier |
| Estimate how a relationship varies with trial attributes | `pair_rsa_design(..., modulation = ...)` + `rsa_model()` | Pair-level relational coefficients; see RSA reference |
| Learn a residual low-rank source-to-target correction | `remap_rrr_model()` | Adaptation and shrinkage toward a naive baseline |
| Model representational mapping, mediation, or a network | `repmap_design()`/`repmap_model()`, `repmed_design()`/`repmed_model()`, `repnet_design()`/`repnet_model()` | Different ReNA model contracts; consult the matching vignette |
| Encode target brain data from grouped aligned features | `feature_sets_design()` + `grouped_ridge_da_model()` or `banded_ridge_da_model()` | Source fit plus target-domain adaptation |
| Adapt Feature RSA to a target domain | `feature_rsa_da_model()` | Family-specific source/target feature and fold contracts |

## Alignment contract

Record which rows belong to each domain, what `link_by`/`key_var` identifies,
whether repeats are averaged or matched one-to-one, and which rows trained an
adapter or preprocessing step. Match by explicit keys, not coincidental row order.
Confirm that every evaluated target has an eligible source candidate and that
features mean the same thing in both domains.

Naive cross-decoding expects separate source `train_data` and target `test_data`
with corresponding design tables. If `link_by` is absent it uses response labels.
ERA supports either separate partitions or combined observations with an explicit
`phase_var`; supply encoding/retrieval levels deliberately. Its `pairing` choice
controls repeat averaging versus one-to-one correspondence. Preserve domain-scoped
run metadata so a run numbered 1 in each session is not conflated accidentally.

ERA's matched similarity, matching-minus-nonmatching item specificity,
identification, and RDM geometry correlation answer different questions. Declare
the candidate set, eligible pairs, run/time nuisance, and association score.
An adjusted item association is not a calibrated causal mediation result.

## Adaptation and held-out evidence

An external target dataset can still leak if its outcomes train an alignment or
adapter. Inspect the actual source/target fold path, including preprocessing and
hyperparameter selection. In the pinned REMAP source, `leave_one_key_out = FALSE`
is the default: the single-fit path builds target prototypes from `test_data`,
fits whitening/adaptation on them, and then scores those target rows. Do not label
that result independent target prediction merely because the data field is named
`test_data`. Some help prose overstates this independence.

With `leave_one_key_out = TRUE` and at least three common keys, the source excludes
the scored key's target prototype from adapter fitting. Verify the actual branch,
eligible keys, and preprocessing provenance; this is item-level holdout, not an
automatic run/participant holdout. State whether the claim concerns new items,
new trials, or a new domain. Recheck this version-specific limitation after updates.

Retain naive-comparator metrics and adapter diagnostics when assessing adaptation.
Check selected rank, shrinkage, pairs used, skipped keys, and fallback. Missing
`rrpack` or inadequate pairs can yield a no-adaptation path; a completed result
does not prove an adapter ran. Compare the same eligible observations and metrics.

For grouped encoding adaptation, `feature_sets_design(target_builder = ...,
target_builder_data = ..., n_test = ...)` can rebuild target predictors separately
inside each outer target fold. A fixed `X_test` is appropriate only when its
construction has valid independent provenance. Do not reuse an alignment trained
on every target outcome and then describe downstream CV as held out.

For a small task, inspect only the chosen family's installed help and example.
Do not mix design objects merely because several constructors contain `design`.
Optional dependencies and supported runners differ by family.

Source/help pointers: `naive_xdec_model`, `era_rsa_design`, `era_rsa_model`,
`remap_rrr_model`, `feature_sets_design`; vignettes `Naive_Cross_Decoding`,
`ERA_RSA_Cross_Decoding`, `REMAP_RRR`, `repmap_model`, `repmed_model`,
`repnet_model`, `Feature_RSA_Domain_Adaptation`.
