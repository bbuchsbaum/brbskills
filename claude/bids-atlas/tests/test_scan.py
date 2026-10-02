#!/usr/bin/env python3
"""Offline tests for bids_atlas.py against a synthetic dataset with planted oddities.

    python skills/bids-atlas/tests/test_scan.py
    BIDS_EXAMPLES=/path/to/bids-examples python skills/bids-atlas/tests/test_scan.py   # adds a crash sweep
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import bids_atlas  # noqa: E402
import make_fixture  # noqa: E402


class Messy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "messy"
        cls.expected = make_fixture.build(cls.root)
        cls.model = bids_atlas.scan(cls.root, [], "auto")
        cls.ids = {f["id"] for f in cls.model["findings"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_planted_findings_detected(self):
        missing = sorted(self.expected - self.ids)
        self.assertEqual(missing, [], f"planted oddities not reported: {missing}")

    def test_no_false_alarms_on_clean_parts(self):
        unexpected = {
            i
            for i in self.ids
            if i in {"no-tr", "no-taskname", "dd-missing", "readme-missing", "no-ped"}
        }
        self.assertEqual(unexpected, set())

    def test_counts(self):
        m = self.model
        self.assertEqual(len(m["subjects"]), 8)
        self.assertEqual(m["sessions"], ["1", "2"])
        self.assertEqual(m["image_states"].get("annex"), 1)
        self.assertEqual(len(m["derivatives"]), 1)
        d = m["derivatives"][0]
        self.assertEqual(
            (d["name"], d["version"], d["kind"]), ("fMRIPrep", "23.2.1", "fmriprep")
        )

    def test_inheritance(self):
        r = next(
            b for b in self.model["bold"] if b["sub"] == "03" and b["task"] == "nback"
        )
        self.assertEqual(r["meta"]["RepetitionTime"], 2.5)
        self.assertTrue(r["meta_src"]["RepetitionTime"].startswith("sub-03/"))
        r = next(
            b for b in self.model["bold"] if b["sub"] == "01" and b["task"] == "rest"
        )
        self.assertEqual(r["meta_src"]["RepetitionTime"], "task-rest_bold.json")

    def test_header_read(self):
        r = self.model["bold"][0]
        self.assertEqual(r["hdr"]["nvols"], 180 if r["task"] == "nback" else 240)
        self.assertAlmostEqual(r["hdr"]["tr"], 2.0)

    def test_confounds_summary(self):
        c = next(
            c for c in self.model["derivatives"][0]["confounds"] if c["sub"] == "06"
        )
        self.assertGreater(c["fd"]["mean"], 0.5)
        self.assertEqual(c["naming"], "snake")
        self.assertEqual(c["compcor"]["aCompCor:combined"]["retained"], 10)
        self.assertEqual(c["n_nonsteady"], 1)
        self.assertEqual(len(c["trace_fd"]), c["n_vols"])

    def test_participants_withheld_by_default(self):
        p = self.model["participants"]
        self.assertFalse(p["included"])
        self.assertEqual(p["rows"], [])
        self.assertNotIn("values", p["summary"]["age"])
        self.assertNotIn("levels", p["summary"]["sex"])

    def test_participants_opt_in(self):
        m = bids_atlas.scan(self.root, [], "yes")
        self.assertTrue(m["participants"]["included"])
        self.assertIn("values", m["participants"]["summary"]["age"])

    def test_render_is_self_contained(self):
        out = Path(self.tmp.name) / "atlas.html"
        bids_atlas.render(self.model, out)
        html = out.read_text()
        self.assertNotIn("__BIDS_ATLAS_DATA__", html)
        self.assertNotRegex(html, r"<script[^>]+src=")
        self.assertNotRegex(html, r"<link[^>]+stylesheet")
        self.assertIn("Synthetic messy n-back study", html)

    def test_script_breakout_is_escaped(self):
        m = json.loads(json.dumps(self.model))
        m["readme"] = "</script><script>alert(1)</script>"
        out = Path(self.tmp.name) / "x.html"
        bids_atlas.render(m, out)
        self.assertEqual(
            out.read_text().count("</script>"), 2
        )  # only the template's own two

    def test_agent_findings_merge(self):
        m = json.loads(json.dumps(self.model))
        bids_atlas.merge_findings(
            m, [{"id": "json-invalid", "severity": "warn", "title": "Reviewed"}]
        )
        ag = [f for f in m["findings"] if f["source"] == "agent"]
        self.assertEqual(ag[0]["id"], "agent-json-invalid")

    def test_mean_fd_not_rounded_before_thresholds(self):
        # Threshold comparisons happen in the page; a rounded mean can flip a run at the boundary.
        for c in self.model["derivatives"][0]["confounds"]:
            if not c.get("fd"):
                continue
            rows = (self.root / c["path"]).read_text().splitlines()
            col = rows[0].split("\t").index("framewise_displacement")
            fd = [float(r.split("\t")[col]) for r in rows[1:] if r.split("\t")[col] != "n/a"]
            self.assertAlmostEqual(c["fd"]["mean"], sum(fd) / len(fd), places=9, msg=c["path"])

    def test_spike_counts_exact(self):
        # Independent of the trace rounding: count straight from the TSV.
        c = next(
            c
            for c in self.model["derivatives"][0]["confounds"]
            if c["sub"] == "06" and c.get("fd")
        )
        rows = (self.root / c["path"]).read_text().splitlines()
        col = rows[0].split("\t").index("framewise_displacement")
        fd = [
            float(r.split("\t")[col]) for r in rows[1:] if r.split("\t")[col] != "n/a"
        ]
        for i in (3, 9, 19):  # 0.20, 0.50, 1.00 mm
            thr = round(0.05 * (i + 1), 2)
            self.assertEqual(c["fd_spikes"][i], sum(v > thr for v in fd), thr)


def _mini_multi_echo(root: Path, doi: bool):
    """Two subjects, multi-echo task with events, MRIQC group table, subject-level physio sidecar."""
    j = lambda p, o: (
        p.parent.mkdir(parents=True, exist_ok=True),
        p.write_text(json.dumps(o)),
    )
    desc = {"Name": "me", "BIDSVersion": "1.8.0"}
    if doi:
        desc["DatasetDOI"] = "doi:10.18112/openneuro.ds999999.v1.0.0"
    j(root / "dataset_description.json", desc)
    (root / "README").write_text("x")
    (root / "participants.tsv").write_text(
        "participant_id\tage\nsub-01\t30\nsub-02\t31\n"
    )
    for e, te in ((1, 0.012), (2, 0.028), (3, 0.044)):
        j(
            root / f"task-a_echo-{e}_bold.json",
            {"TaskName": "a", "RepetitionTime": 2.0, "EchoTime": te},
        )
    q = ["bids_name\ttsnr\tfd_mean\tsize_t"]
    for s in ("01", "02"):
        f = root / f"sub-{s}" / "func"
        f.mkdir(parents=True)
        for e in (1, 2, 3):
            (f / f"sub-{s}_task-a_echo-{e}_bold.nii.gz").write_bytes(b"")
            q.append(f"sub-{s}_task-a_echo-{e}_bold\t{50 + e}\t0.1\t100")
        (f / f"sub-{s}_task-a_events.tsv").write_text(
            "onset\tduration\tcond\n10\t5\tx\n150\t5\ty\n205\t5\tx\n"
        )
        j(
            root / f"sub-{s}" / f"sub-{s}_task-a_physio.json",
            {"SamplingFrequency": 50, "StartTime": 0, "Columns": ["cardiac"]},
        )
    mq = root / "derivatives" / "mriqc"
    j(
        mq / "dataset_description.json",
        {
            "Name": "MRIQC",
            "BIDSVersion": "1.4.0",
            "DatasetType": "derivative",
            "GeneratedBy": [{"Name": "MRIQC", "Version": "23.1.0"}],
        },
    )
    (mq / "group_bold.tsv").write_text("\n".join(q) + "\n")
    (mq / "sub-01_task-a_echo-1_bold.html").write_text("<html></html>")


class MultiEchoMriqc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "ds999999"
        _mini_multi_echo(cls.root, doi=False)
        cls.model = bids_atlas.scan(cls.root, [], "auto")
        cls.f = {f["id"]: f for f in cls.model["findings"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_counts_are_per_run_not_per_echo(self):
        self.assertEqual(self.f["no-ped"]["count"], 2)
        self.assertEqual(self.model["tasks"]["a"]["runs"], 2)
        self.assertEqual(self.f["events-notype"]["count"], 2)

    def test_echo_times_collapse(self):
        te = self.model["consistency"]["a"]["EchoTime"]
        self.assertEqual(te, [[[0.012, 0.028, 0.044], 2]])
        self.assertNotIn("hetero-a-EchoTime", self.f)

    def test_inferred_condition_column(self):
        ev = self.model["bold"][0]["events"]
        self.assertEqual(ev["type_column_inferred"], "cond")

    def test_subject_level_sidecar_is_bids(self):
        self.assertNotIn("nonbids", self.f)

    def test_mriqc_iqms_and_scan_length(self):
        d = self.model["derivatives"][0]
        self.assertEqual(
            (d["kind"], len(d["iqms"]), len(d["reports"])), ("mriqc", 6, 1)
        )
        r = self.model["bold"][0]
        self.assertEqual(
            (r["nvols"], r["nvols_source"], r["scan_seconds"]),
            (100, "MRIQC size_t + dummy_trs", 200.0),
        )
        # last event ends at 210 s > 200 s + 1 TR
        self.assertEqual(self.f["events-past-end"]["count"], 2)

    def test_folder_name_alone_does_not_release_participants(self):
        p = self.model["participants"]
        self.assertFalse(p["included"])
        self.assertIn("folder name", p["reason"].lower())

    def test_openneuro_doi_releases_participants(self):
        root = Path(self.tmp.name) / "withdoi"
        _mini_multi_echo(root, doi=True)
        self.assertTrue(bids_atlas.scan(root, [], "auto")["participants"]["included"])


class ReviewRegressions(unittest.TestCase):
    """Inputs from the code review that the hill-climb specimens never exercised."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "ds"

    def tearDown(self):
        self.tmp.cleanup()

    def _mini(self, rec=False):
        r = self.root
        (r / "sub-01" / "func").mkdir(parents=True)
        (r / "dataset_description.json").write_text(json.dumps({"Name": "x", "BIDSVersion": "1.9.0"}))
        (r / "README").write_text("x")
        (r / "task-a_bold.json").write_text(json.dumps({"TaskName": "a", "RepetitionTime": 2.0}))
        ent = "_rec-norm" if rec else ""
        make_fixture.nifti(r / "sub-01" / "func" / f"sub-01_task-a{ent}_run-1_bold.nii.gz", 50, 2.0)
        prep = r / "derivatives" / "fmriprep"
        (prep / "sub-01" / "func").mkdir(parents=True)
        (prep / "dataset_description.json").write_text(json.dumps({"Name": "f", "DatasetType": "derivative", "GeneratedBy": [{"Name": "fMRIPrep", "Version": "23.2.1"}]}))
        tsv, meta = make_fixture.confounds(__import__("random").Random(1), 50, 0.03, 1)
        (prep / "sub-01" / "func" / f"sub-01_task-a{ent}_run-1_desc-confounds_timeseries.tsv").write_text(tsv)
        return r

    def test_corrupt_gzip_does_not_crash(self):
        r = self._mini()
        (r / "sub-01" / "func" / "sub-01_task-a_run-1_bold.nii.gz").write_bytes(b"\x1f\x8b\x08\x00" + b"\x00" * 6 + b"garbage" * 80)
        bids_atlas.scan(r, [], "no")

    def test_rec_entity_pairs_raw_and_confounds(self):
        m = bids_atlas.scan(self._mini(rec=True), [], "no")
        ids = {f["id"] for f in m["findings"]}
        self.assertFalse({i for i in ids if i.startswith(("conf-missing", "conf-noraw"))}, ids)
        self.assertEqual(m["bold"][0]["key"], m["derivatives"][0]["confounds"][0]["key"])

    def test_reference_mentioning_openneuro_is_not_release(self):
        r = self._mini()
        (r / "participants.tsv").write_text("participant_id\tage\nsub-01\t30\n")
        (r / "dataset_description.json").write_text(json.dumps({"Name": "x", "BIDSVersion": "1.9.0", "ReferencesAndLinks": ["Task from https://openneuro.org/datasets/ds000030"]}))
        self.assertFalse(bids_atlas.scan(r, [], "auto")["participants"]["included"])

    def test_empty_events_file_is_reported(self):
        r = self._mini()
        (r / "sub-01" / "func" / "sub-01_task-a_run-1_events.tsv").write_text("")
        m = bids_atlas.scan(r, [], "no")
        self.assertIn("events-empty", {f["id"] for f in m["findings"]})
        self.assertEqual(m["tasks"]["a"]["events"], 0)

    def test_derivative_passed_twice_is_scanned_once(self):
        r = self._mini()
        m = bids_atlas.scan(r, [r / "derivatives" / "fmriprep"], "no")
        self.assertEqual(len(m["derivatives"]), 1)

    def test_bom_sidecar_parses(self):
        r = self._mini()
        (r / "task-a_bold.json").write_bytes("\ufeff".encode() + json.dumps({"TaskName": "a", "RepetitionTime": 2.0}).encode())
        ids = {f["id"] for f in bids_atlas.scan(r, [], "no")["findings"]}
        self.assertFalse({"json-invalid", "no-tr"} & ids, ids)

    def test_deeply_nested_json_is_invalid_not_crash(self):
        r = self._mini()
        (r / "sub-01" / "func" / "sub-01_task-a_run-1_bold.json").write_text("[" * 100000 + "]" * 100000)
        bids_atlas.scan(r, [], "no")

    def test_render_survives_non_utf8_text(self):
        r = self._mini()
        m = bids_atlas.scan(r, [], "no")
        m["readme"] = "bad \udcff name"
        bids_atlas.render(m, Path(self.tmp.name) / "out" / "x.html")


@unittest.skipUnless(
    os.environ.get("BIDS_EXAMPLES"), "set BIDS_EXAMPLES to sweep bids-examples"
)
class ExamplesSweep(unittest.TestCase):
    def test_no_crash(self):
        root = Path(os.environ["BIDS_EXAMPLES"])
        tmp = Path(tempfile.mkdtemp())
        for ds in sorted(
            p
            for p in root.iterdir()
            if p.is_dir() and (p / "dataset_description.json").exists()
        ):
            with self.subTest(ds=ds.name):
                m = bids_atlas._clean_nan(bids_atlas.scan(ds, [], "auto"))
                bids_atlas.render(m, tmp / f"{ds.name}.html")


if __name__ == "__main__":
    unittest.main(verbosity=2)
