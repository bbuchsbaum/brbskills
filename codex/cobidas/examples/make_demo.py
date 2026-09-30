#!/usr/bin/env python3
"""Create a SYNTHETIC reporting fixture, NOT an MRI analysis or human study."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import sys

BUNDLE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cobidas", BUNDLE / "scripts/cobidas.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def create(project: Path) -> dict:
    project.mkdir(parents=True, exist_ok=True)
    root = c.initialize(project, ["task", "glm"])
    evdir = project / "evidence"
    evdir.mkdir()
    configuration = {"synthetic_fixture": True, "no_images_processed": True,
       "smoothing": {"performed": False, "reason": "Illustrative unsmoothed model branch"},
       "confounds": {"family": "motion24", "definition": "Six rigid-body parameters, their first differences, and squares of those twelve columns",
                     "first_difference_boundary": "zero at first retained volume", "n_columns": 24},
       "temporal": {"basis": "Legendre polynomials", "degree": 2, "per_run": True,
                    "includes_intercept": True, "bandpass_performed": False,
                    "fit_strategy": "Nuisance terms included jointly in the task GLM"},
       "hrf": {"family": "SPM canonical HRF", "temporal_derivative": True,
               "dispersion_derivative": False}}
    c.write(evdir / "resolved.json", configuration)
    c.write(evdir / "input-manifest.json", {"synthetic_fixture": True, "members": ["fabricated-run-A", "fabricated-run-B"], "unit": "runs"})
    c.write(evdir / "output-manifest.json", {"synthetic_fixture": True, "artifacts": ["fabricated-model-object"], "no_real_model_fit": True})
    c.write(evdir / "validation.json", {"synthetic_fixture": True, "purpose": "Exercise reporting records only; no scientific validation asserted"})
    def ev(name, locator="/"):
        return {"path": "evidence/" + name, "locator": locator, "kind": "synthetic_fixture"}
    activity = {"id": "fixture-receipt", "kind": "activity", "scope": "analysis-main", "by": "synthetic-fixture-builder",
                "status": "succeeded", "software": [{"name": "synthetic-fixture-builder-not-mri-software", "version": "0.1.0"}],
                "invocation": {"fixture_only": True, "no_mri_analysis_executed": True},
                "inputs": [ev("input-manifest.json")], "outputs": [ev("output-manifest.json")],
                "validation": {"status": "passed", "evidence": [ev("validation.json")]}, "depends_on": []}
    facts = []
    for key, locator in [("preprocessing.smoothing", "smoothing"), ("denoising.confounds", "confounds"),
                         ("denoising.temporal", "temporal"), ("model.hrf", "hrf")]:
        facts.append({"id": "fixture-" + locator, "kind": "fact", "scope": "analysis-main", "by": "synthetic-fixture-builder",
                      "key": key, "phase": "actual", "status": "known", "value": configuration[locator],
                      "basis": "observed", "evidence": [ev("resolved.json", "/" + locator)],
                      "activity_ids": ["fixture-receipt"], "supersedes": [],
                      "notes": "Actual describes the fabricated record state, not a real MRI execution."})
    # Preserve a partially recovered field without presenting it as complete.
    facts[-1]["missing_details"] = ["HRF basis orthogonalization setting"]
    membership = {"id": "fixture-members", "kind": "fact", "scope": "analysis-main", "by": "synthetic-fixture-builder",
                  "key": "scope.members", "phase": "actual", "status": "known",
                  "value": {"manifest": "evidence/input-manifest.json", "unit": "runs", "n_units": 2},
                  "basis": "derived", "evidence": [ev("input-manifest.json", "/members")], "activity_ids": [], "supersedes": []}
    c.import_records(root, [activity, *facts, membership])
    report = c.audit(root)
    draft = {"audit_digest": report["audit_digest"], "paragraphs": [{
        "id": "synthetic-preprocessing-example", "destination": "methods", "section": "Synthetic illustration — not a real study",
        "text": "In this synthetic task-GLM example, no spatial smoothing was applied. Twenty-four motion nuisance regressors comprised the six rigid-body motion parameters, their first differences, and the squares of those twelve columns. Run-specific Legendre polynomials through degree two were included jointly with the task and motion regressors. Task responses were represented using the SPM canonical haemodynamic response function and its temporal derivative.",
        "claim_ids": ["fixture-smoothing", "fixture-confounds", "fixture-temporal", "fixture-hrf"]}, {
        "id": "synthetic-supplement", "destination": "supplement", "section": "Synthetic temporal details",
        "text": "The first-difference motion columns were set to zero at the first retained volume. The polynomial basis included the intercept, and no band-pass filtering was performed in this synthetic specification.",
        "claim_ids": ["fixture-confounds", "fixture-temporal"]}]}
    c.write(project / "draft.json", draft)
    outcome = c.build(root, draft)
    (project / "README.md").write_text("# Synthetic fixture only\n\nNo human data, images, model fitting, preprocessing or scientific QC were performed. All receipts and facts are fabricated solely to demonstrate the reporting contract. Never reuse them as study evidence. The resulting paragraph is deliberately incomplete; inspect gaps.md. The SPM HRF name in the illustrative prose is not a claim that SPM was executed. The HRF fact explicitly lists the unknown orthogonalization setting in missing_details, so the gap remains visible even though the known HRF family can be described.\n")
    return outcome


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True, help="Directory with no existing reporting/cobidas")
    args = p.parse_args()
    try:
        print(create(args.output.resolve()))
    except (OSError, c.RecordError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
