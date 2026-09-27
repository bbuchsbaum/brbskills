# Render from a reviewed map manifest. This function does not perform inference.
render_reviewed_montage <- function(maps, output, background,
                                    interactive_voxels = FALSE,
                                    disclosure_approved = FALSE) {
  if (!requireNamespace("neuromosaic", quietly = TRUE)) stop("neuromosaic is required")
  required <- c("analysis_id", "map_id", "path", "role", "quantity", "distribution", "label")
  if (!is.data.frame(maps) || !all(required %in% names(maps)) || !nrow(maps)) stop("Incomplete map manifest")
  if (anyDuplicated(maps$map_id)) stop("Map IDs must be unique")
  if (!all(file.exists(maps$path))) stop("Map files are missing")
  if (file.exists(output)) stop("Refusing to overwrite report")
  # Spatial/quantity/correction checks must already be documented in the plan.
  if (interactive_voxels) {
    if (!isTRUE(disclosure_approved)) stop("Explicit recoverable-voxel disclosure approval required")
    neuromosaic::render_montage_report(maps, output, bg = background,
      interactive = neuromosaic::montage_interactive(assets = "embed",
                    controls = c("threshold", "palette", "opacity")))
  } else neuromosaic::render_montage_report(maps, output, bg = background)
  if (!file.exists(output) || file.info(output)$size <= 0) stop("No nonempty report produced")
  invisible(normalizePath(output, mustWork = TRUE))
}
