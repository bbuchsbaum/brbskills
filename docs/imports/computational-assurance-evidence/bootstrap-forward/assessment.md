# Bounded forward assessment: repeated-measures percentile bootstrap

## Exact request

Assess whether this percentile bootstrap interval can be described as a 95%
confidence interval for the population mean participant response. Participants
each contributed four readings. Review the code and synthetic data, execute
bounded checks if useful, and report what the evidence does and does not
support. There is no prediction task. Do not modify source or bring in private
data.

## Scope and identity

Read only:

* `skills/scientific-check/SKILL.md` (workflow instruction)
* `tests/fixtures/bootstrap.py`
* `tests/fixtures/repeated_measurements.csv`

SHA-256:

* `bootstrap.py`: `27147b41919d3c04b3b253d7e7fd1645f473287abaeba434b5929004a23ddcd4`
* `repeated_measurements.csv`: `bf388fb1e5dc4d0cca57d6dcf3e7051b5a1da7afc4cd2700a6965aa7aefebfbf`

Actual hash-command stdout (after a non-substantive locale warning):

```text
27147b41919d3c04b3b253d7e7fd1645f473287abaeba434b5929004a23ddcd4  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/scientific-check/tests/fixtures/bootstrap.py
bf388fb1e5dc4d0cca57d6dcf3e7051b5a1da7afc4cd2700a6965aa7aefebfbf  /private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/scientific-check/tests/fixtures/repeated_measurements.csv
```

No source files were changed. Only Python 3 standard-library modules were
used; no network, external compute, dependencies, private data, or simulation
study was used.

## Code and data review

`confidence_interval` takes all 48 `response` cells into one vector and, in
each replicate, samples 48 cells independently with replacement. It then
returns the empirical 2.5% and 97.5% quantiles of the resampled cell means.
The `participant` and `reading` columns are unused.

The fixture has 12 participants, each with four readings. Within a participant,
the readings differ only by -0.15, -0.05, 0.05, and 0.15 around that
participant's mean; between-participant means range from -11 to 11. Thus the
four readings are deliberately strongly clustered rather than interchangeable
independent participant draws. All participants have the same number of
readings, so the observed flat mean happens to equal the mean of participant
means (0), but that equality does not make cell-level resampling valid for its
uncertainty.

## Executed bounded check

The following command was executed (exit status 0):

```sh
python3 -c 'import csv, importlib.util, statistics; p="/private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/scientific-check/tests/fixtures/bootstrap.py"; d="/private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/scientific-check/tests/fixtures/repeated_measurements.csv"; spec=importlib.util.spec_from_file_location("bootstrap",p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); rows=list(csv.DictReader(open(d,newline=""))); by={}; [by.setdefault(r["participant"],[]).append(float(r["response"])) for r in rows]; pm=[statistics.mean(v) for v in by.values()]; print("flat_code_ci", m.confidence_interval(rows)); print("n_readings",len(rows),"n_participants",len(pm),"sample_mean",statistics.mean(float(r["response"]) for r in rows)); print("participant_means",pm); print("participant_mean_sample_variance",statistics.variance(pm)); import random; rng=random.Random(2026); e=sorted(statistics.mean(rng.choices(pm,k=len(pm))) for _ in range(999)); print("cluster_percentile_ci",(e[int(.025*999)],e[int(.975*999)])); print("flat_sample_variance",statistics.variance(float(r["response"]) for r in rows)); print("flat_mean_bootstrap_sd",statistics.stdev(sorted([0]) + [0]) if False else "not_estimated")'
```

Actual stdout:

```text
flat_code_ci (-2.00625, 1.96875)
n_readings 48 n_participants 12 sample_mean 0.0
participant_means [-11.0, -9.0, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
participant_mean_sample_variance 52.0
cluster_percentile_ci (-4.333333333333333, 3.8333333333333335)
flat_sample_variance 48.693617021276594
flat_mean_bootstrap_sd not_estimated
```

The independent comparison resamples the 12 participant means (equivalently,
for these balanced data, resamples whole four-reading participant clusters) and
then computes their mean. It uses the same finite-replicate percentile recipe
and seed only to isolate the resampling unit; it is not a calibration study.
Its interval is materially wider than the code's cell-resampled interval.

## Conclusion

The supplied interval, `(-2.00625, 1.96875)`, should **not** be described as a
95% confidence interval for the population mean participant response. The
estimator's center equals the participant-level sample mean in this balanced
fixture, but the bootstrap resamples 48 repeated readings as independent
units. That treats the four values within each participant as four independent
participants and understates sampling uncertainty when, as here, most variation
is between participants.

For the stated participant-population estimand, a participant/cluster bootstrap
would resample the 12 participants (retaining their four readings) and compute
the mean participant response in each replicate. In this fixture, the bounded
reference produces `(-4.333333333333333, 3.8333333333333335)`, showing the
consequential dependence on the resampling unit. This is evidence about the
formulation on the supplied fixture, not a claim that that particular interval
has exact 95% coverage.

Even a correctly clustered percentile bootstrap only supports an approximate
95% confidence-interval interpretation under further assumptions: participants
are independent and representative draws from the target population, the
participant-level estimand and handling of the four readings are prespecified,
and the finite 12-participant bootstrap adequately approximates the sampling
distribution. No repeated-dataset coverage experiment, robustness assessment,
or real-data generalization was run, so exact nominal coverage and adequacy for
any external study remain unresolved.

## Final response

No. The supplied percentile interval cannot be called a 95% confidence interval
for the population mean participant response: it bootstraps the 48 readings as
independent although each set of four belongs to one participant. Its point
estimate is numerically the participant mean here only because the design is
balanced. A bounded participant-cluster reference gave `(-4.3333, 3.8333)`,
versus the code's `(-2.00625, 1.96875)`, which is consistent with the code
understating uncertainty. A participant-level interval would still be
approximate and depends on independent, representative participants and on
the adequacy of a 12-participant bootstrap; this review did not test coverage
or establish applicability beyond the synthetic fixture.
