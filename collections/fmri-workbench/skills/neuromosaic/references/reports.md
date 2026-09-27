# Report construction

The source-reviewed package supports atlas-annotated cluster reports, grouped
map montages and a Shiny explorer. The native CLI lives at
`system.file("exec", "neuromosaic", package="neuromosaic")` after installation.
Inspect --help before using version-specific CLI flags. Do not modify PATH or
shell startup files automatically; call the resolved wrapper path directly.

For related maps use the documented R manifest:

```r
maps <- data.frame(
  analysis_id = "A_minus_B",
  map_id = c("A_B_z", "A_B_estimate", "A_B_se"),
  path = c("z.nii.gz", "beta.nii.gz", "se.nii.gz"),
  role = c("primary", "auxiliary", "auxiliary"),
  quantity = c("test_statistic", "estimate", "standard_error"),
  distribution = c("z", NA, NA),
  label = c("Z statistic", "Effect estimate", "Standard error"))
neuromosaic::render_montage_report(maps, "report.html", bg = anatomical_volume)
```

The z label is illustrative: use the actual statistic distribution. Built-in
profiles choose rendering behavior; inspect defaults and explicitly communicate
their interpretation. Custom quantities use `montage_map_profile()` when supported.
Inferences are carried by the statistical artifact, not by a display profile.

For cluster reports, the CLI has a structural route such as:

```sh
neuromosaic report --stat-map stats/z.nii.gz --atlas Schaefer400   --threshold 3.1 --min-cluster-size 10 --out report.html
```

These numbers are an example of **display settings**, not recommended cutoffs or
multiple-comparison control. Before using this path, establish distribution,
sidedness, mask/correction and cluster definition from the inference manifest.
Use verified installed options or labeled masked display copies to respect a
rejection mask. Do not invent a `correction_mask` argument.

Atlas labels depend on atlas version and spatial registration. Use nearest-label
resampling for discrete labels only with a justified explicit transform. Resampling
labels for visualization is not evidence that statistical maps are normalized.
Display anatomical uncertainty/overlap and avoid reverse-inference claims from a
parcel name alone. A selected-cluster behavioral scatterplot is descriptive unless
selection is independent or validated out of sample.

HTML is the simplest default. QMD creates source plus a report-data sidecar;
PDF requires the documented Pandoc/LaTeX tools. Verify dependencies before
promising those formats. Inspect rendered output for missing panels, labels,
colorbar units, orientation, thresholds and empty results. Report external asset
requirements, not just the main file.

Optional interactive configuration:

```r
neuromosaic::render_montage_report(
  maps, "report.html", bg = anatomical_volume,
  interactive = neuromosaic::montage_interactive(
    assets = "embed", controls = c("threshold", "palette", "opacity")))
```

Embed retains recoverable voxel arrays; bundle creates companion interactive
assets intended to be served together. Static output remains authoritative and a
fallback; interactive semantic parity is not pixel identity. Obtain appropriate
disclosure approval before creating/sharing these richer artifacts.
