"""Small end-to-end regression suite: python3 tests/test_compare_anchors.py."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_anchors.py"


class AnchorComparisonTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="compare-anchors-")
        self.addCleanup(self.directory.cleanup)
        self.before = Path(self.directory.name) / "before.md"
        self.after = Path(self.directory.name) / "after.md"

    def compare(self, before, after, *locks):
        self.before.write_text(before, encoding="utf-8")
        self.after.write_text(after, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), str(self.before), str(self.after), "--json"]
        for literal in locks:
            command.extend(["--lock", literal])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["advisory"])
        self.assertTrue(report["semantic_equivalence_not_assessed"])
        self.assertTrue(all(f["status"] == "review_candidate" for f in report["findings"]))
        return report

    @staticmethod
    def anchors(report, category):
        return {f["anchor"] for f in report["findings"] if f["category"] == category}

    def test_requirement_and_threshold_changes(self):
        report = self.compare("Each reviewer should use p < 0.05.",
                              "Each reviewer must use p < 0.5.")
        self.assertEqual(self.anchors(report, "marker_modality"), {"should", "must"})
        self.assertEqual(self.anchors(report, "numeric_expression"), {"<0.05", "<0.5"})

    def test_signs_comparators_scientific_notation_and_units(self):
        report = self.compare("p<.05; delay ≥2.0e-3s; mass −3.2mg; field 3 T.",
                              "p>.05; delay ≥2.0e-3ms; mass +3.2mg; field 3 mT.")
        numbers = self.anchors(report, "numeric_expression")
        for old, new in (("<.05", ">.05"), ("≥2.0e-3s", "≥2.0e-3ms"),
                         ("−3.2mg", "+3.2mg"), ("3T", "3mT")):
            with self.subTest(old=old, new=new):
                self.assertIn(old, numbers)
                self.assertIn(new, numbers)

    def test_literal_locks_are_exact_and_include_code(self):
        report = self.compare("Use `SampleA` and sampleA.", "Use `SampleB` and sampleA.",
                              "SampleA", "sampleA")
        self.assertEqual(self.anchors(report, "locked_literal"), {"SampleA"})
        changed = next(f for f in report["findings"] if f["category"] == "locked_literal")
        self.assertEqual((changed["before_count"], changed["after_count"]), (1, 0))

    def test_rewrap_preserves_inventories(self):
        report = self.compare("Each reviewer should not proceed unless all checks pass.\nDelay: 5 ms.",
                              "Each reviewer should\nnot proceed unless\nall checks pass. Delay: 5\nms.")
        self.assertFalse(report["findings"])

    def test_repeated_anchors_and_overlapping_locks(self):
        report = self.compare("Each 5 ms pulse, each 5 ms pulse. KEEP KEEP. aaa",
                              "Each 5 ms pulse. KEEP. aa", "KEEP", "aa", "KEEP")
        for category, anchor in (("numeric_expression", "5ms"), ("marker_quantifier", "each"),
                                 ("locked_literal", "KEEP"), ("locked_literal", "aa")):
            with self.subTest(category=category, anchor=anchor):
                matches = [f for f in report["findings"]
                           if f["category"] == category and f["anchor"] == anchor]
                self.assertEqual(len(matches), 1)
                self.assertEqual((matches[0]["before_count"], matches[0]["after_count"]), (2, 1))

    def test_code_and_links_are_compared_but_masked_from_prose(self):
        report = self.compare("Use `mode=1`. [Help](https://example.org/1)\n"
                              "```python\nif x < 0.05: pass\n```\nhttps://example.org/raw1\n",
                              "Use `mode=2`. [Help](https://example.org/2)\n"
                              "```python\nif x < 0.5: pass\n```\nhttps://example.org/raw2\n")
        categories = {f["category"] for f in report["findings"]}
        self.assertEqual(categories, {"inline_code", "fenced_code", "link_destination", "raw_url"})

    def test_marker_context_and_negation(self):
        report = self.compare("First line.\nWe can proceed unless all agree.\n",
                              "First line.\nWe can’t proceed\nunless all agree.\n")
        negation = next(f for f in report["findings"] if f["category"] == "marker_negation")
        self.assertEqual(negation["after"][0]["line"], 2)
        self.assertIn("proceed unless", negation["after"][0]["context"])

    def test_relationship_reversal_is_not_a_semantic_verdict(self):
        report = self.compare("All 20 reviewers may score 5 authors.",
                              "All 20 authors may score 5 reviewers.")
        self.assertFalse(report["findings"])
        self.assertTrue(report["semantic_equivalence_not_assessed"])
        self.assertTrue(report["limitations"])

    def test_scientific_wording_is_not_style_policed(self):
        report = self.compare("We used robust regression to estimate the association.",
                              "Robust regression estimated the association.")
        self.assertFalse(report["findings"])

    def test_missing_input_is_an_error(self):
        self.after.write_text("A revision.", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.before), str(self.after),
                                 "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertIn("input_error", report)
        self.assertTrue(report["semantic_equivalence_not_assessed"])


if __name__ == "__main__":
    unittest.main()
