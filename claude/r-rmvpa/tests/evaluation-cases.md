# Behavioral evaluation cases

Use fresh sessions with only the stated fixture and installed package available.
For implicit selection, expose the skill metadata alongside the ordinary skill
catalog without naming the skill. For workflow behavior, invoke it explicitly.
Keep writes in a disposable directory; no real data, cluster work, installation,
publication, or package edits are needed. Do not supply grading criteria to the
evaluated agent. Record product/model, prompt, selected files, artifacts, checks,
and pass/fail reasons. A case listed here is not a passed evaluation.

## Core cases

| ID | User request and fixture | Observable acceptance criteria |
|---|---|---|
| D1 | “Use rMVPA to decode two conditions from 4 runs of beta maps. Make a runnable synthetic regional example.” No data. | Uses real constructors, factor labels, whole-run folds, geometry-compatible labels; example executes and reports predictions without claiming significance. |
| D2 | “Each row is one trial; I standardized all beta rows, selected the best voxels using all labels, then used random 10-fold CV. Review my rMVPA plan.” | Identifies upstream leakage and run dependence; moves fitted transforms/selection into training folds; does not claim changing the CV function alone fixes the analysis. |
| D3 | “Use split_by = subject to test generalization to new participants.” Aligned trial metadata. | Explains scoring partitions versus training separation and requests/constructs participant-held-out folds. |
| R1 | “My rMVPA RSA has semantic, visual and run-nuisance RDMs. Give me a permutation p-value for semantic after controlling the others.” | Does not mislabel joint-null permutations or one selected metric as conditional inference; explains the missing supported inferential route while preserving the requested estimand. |
| R2 | “Encoding and retrieval rows are combined. Estimate how matching-item similarity varies with retrieval vividness.” Explicit row/item/run metadata. | Uses pair indices and modulation with similarity/beta semantics; handles nuisance/identifiability and participant-level inference limits. |
| E1 | “Fit visual and semantic feature sets to 4 runs of voxel responses with rMVPA; estimate held-out band contributions.” Synthetic matrices. | Uses feature_sets_design, nested block-aware banded ridge and its runner; interprets retuned dropout effects as nonadditive and allows negative values. |
| E2 | “My Feature RSA F matrix contains PCA scores. Speed it up and save OOF predictions from every overlapping searchlight.” | Preserves score geometry deliberately; distinguishes tuning changes from implementation speedups; notices prediction-retention restriction and offers regional retention or scalar maps. |
| P1 | “Fit pattern_model on these trials, then use the same trials with new row IDs to confirm the significant voxels and supported rank.” Synthetic data. | Rejects the independence claim, does not invent rank significance, offers descriptive/CV outputs or a truly independent confirmation plan. |
| P2 | “Interpolate each subject's confirmed SE map to a common grid, then call pattern_group.” Confirmation metadata. | Identifies one-to-one mapping/full-covariance contract and missing uncertainty transport; does not blindly pool interpolated SEs. |
| X1 | “Compare REMAP to naive cross-decoding; target alignment was fitted using every target response.” Paired item metadata. | Identifies target leakage; checks adapter fit/fallback and compares matched eligible outcomes, not just successful result objects. |
| X2 | “I supplied test_data to remap_rrr_model with default options. Is its target accuracy automatically held out?” Pinned source available. | Identifies default single-fit target-prototype reuse, checks actual LOKO branch and distinguishes item holdout from run/participant generalization. |
| C1 | “Write a custom rMVPA searchlight callback that compares train and external-test data.” Small synthetic images. | Uses sl_info$test_data and consistent scalar metrics, checks errors; does not assume the callback wrapper supplies CV or inference. |
| V1 | “The checkout documents rsa_model(statistic='beta') but my installed function rejects statistic.” Older-install signature supplied. | Inspects loaded path and formals, distinguishes checkout/installed versions, offers compatible work or an explicit dependency update; no namespace monkey patch or invented API. |

## Selection exclusions

| ID | Prompt | Expected behavior |
|---|---|---|
| N1 | “Fit a random-intercept model with lme4.” | Does not select r-rmvpa. |
| N2 | “Run fMRIPrep on raw BIDS data.” | Does not select r-rmvpa as the preprocessing workflow. |
| N3 | “Build a classifier in scikit-learn.” | Does not substitute rMVPA. |
| N4 | “Explain representational similarity analysis conceptually; no software.” | Does not require the rMVPA package workflow. |

Compare matched with-skill and no-skill trials before claiming benefit. Testing an
explicit skill invocation does not measure automatic discovery. Repeat on the
actual Codex and Claude models intended for distribution; same-model subagents
are only bounded forward checks.
