---
type: llm
---

PASS only if: Uses public write_results by_stat with contrast beta and SE, exact selectors and returned paths; verifies ContrastOrder for both files and all subjects; pairs by keys before supplying explicit subjects; checks every grid/affine and coverage masks, preserving real zeros and explicit missingness; does not treat by_contrast statistic volumes or raw regressor betas as contrast maps; distinguishes SE from variance and preserves independent subject units; keeps group model choice explicit.
FAIL if these conditions are not met or if results are fabricated.
