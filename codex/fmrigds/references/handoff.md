# First-level to GDS bridge

For fmrireg NIfTI outputs, follow the [tested NIfTI handoff](nifti-handoff.md):
separate beta/SE files, JSON contrast order, explicit subject pairing and verified
grid/coverage masks. Use `gds(nifti_source(...), format="nifti", mask=...)`.
Validate one source, then one subject/contrast, before fan-out. Retain
sample/subject/contrast identity. Other arrays/tables and documented image/HDF5
adapters remain available; do not assume a converter from `collect_results()`.

For a modest ROI example, convert a verified fmrireg contrast reducer table to:

```r
# `x` must already contain the requested contrast only, with validated semantics.
tab <- data.frame(sample = x$voxel, subject = x$job_id,
                  contrast = x$contrast, beta = x$estimate, var = x$se^2)
stopifnot(!anyDuplicated(tab[c("sample", "subject", "contrast")]),
          all(is.finite(tab$beta)), all(is.finite(tab$var)), all(tab$var > 0))
write.csv(tab, path, row.names = FALSE)
plan <- fmrigds::gds(path)
```

The exact reducer contrast-column name must be inspected; this code deliberately
assumes a normalized `x$contrast`, not a claim about every reducer version. Do not
replace unknown labels with an invented fixed string. A numeric voxel index is
only valid across subjects when its grid/mask/order is common and verified. For
voxelwise files retain a proper space object or original template/mask/index
mapping; a label alone cannot reconstruct anatomy. A zero variance needs review,
not arbitrary epsilon insertion.

Small ROI checks may fail on missing data intentionally. For real partial coverage,
use an approved explicit missingness policy supported by the selected adapter/
reducer and record actual samplewise N rather than blanket deletion. Check mask
lattice dimensions, affine, units and ordering, not just total number of voxels.

SE/variance are for the **contrast**, including relevant coefficient covariance.
Do not compute a multi-condition contrast variance by summing coefficient
variances while ignoring covariance. Repeated contrast/session inputs need their
within-person statistical dependence represented or reduced with justification.

Native fmrigds adapters ingest NIfTI, HDF5/fmristore and tabular inputs. Verify the
selected adapter's file/assay mapping and serialize it in the analysis. The NIfTI
recipe is one concrete route, not a universal image adapter. Return a manifest of
effects, uncertainties, spatial identity, scientific meaning and provenance.
