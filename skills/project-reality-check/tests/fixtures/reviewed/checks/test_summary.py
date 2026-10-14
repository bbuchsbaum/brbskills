import unittest

from summary import summarize


class SummaryTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(summarize([4, 10, 16]), {"count": 3, "mean": 10})

    def test_empty(self):
        with self.assertRaises(ValueError):
            summarize([])

    def test_nonnumeric(self):
        with self.assertRaises(ValueError):
            summarize(["bad"])
