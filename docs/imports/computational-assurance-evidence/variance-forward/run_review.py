"""Stdlib-only, independent checks for the supplied variance candidate.

This reviewer intentionally exits zero after printing results: mismatches are
review evidence, not a test-suite failure to be repaired in this task.
"""

from fractions import Fraction
import math


INPUT = "/private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py"


namespace = {"__name__": "candidate_variance"}
with open(INPUT, "r", encoding="utf-8") as handle:
    exec(compile(handle.read(), INPUT, "exec"), namespace)
population_variance = namespace["population_variance"]


def exact_population_variance(values):
    """Exact variance over the precise binary-float observations."""
    fractions = [Fraction.from_float(value) for value in values]
    mean = sum(fractions) / len(fractions)
    return sum((value - mean) ** 2 for value in fractions) / len(fractions)


def matches(candidate, expected):
    if isinstance(expected, Fraction):
        expected = float(expected)
    return math.isfinite(candidate) and math.isclose(candidate, expected, rel_tol=1e-15, abs_tol=0.0)


cases = [
    ("ordinary symmetric values", [-2.0, 0.0, 2.0]),
    ("single observation", [42.5]),
    ("large shared offset with representable spacing", [1.0e16, 1.0e16 + 2.0]),
    ("large finite constant", [1.0e308, 1.0e308]),
]

print("exact-oracle cases")
for label, values in cases:
    expected = exact_population_variance(values)
    actual = population_variance(values)
    print(f"{label}: values={values!r}")
    print(f"  exact={float(expected)!r}; candidate={actual!r}; match={matches(actual, expected)}")

base = [1.25, -2.5, 3.75, 4.5]
base_result = population_variance(base)
translated_result = population_variance([value + 10.0 for value in base])
scaled_result = population_variance([-3.0 * value for value in base])
permuted_result = population_variance(list(reversed(base)))
print("metamorphic ordinary-scale cases")
print(f"translation: baseline={base_result!r}; translated={translated_result!r}; match={math.isclose(base_result, translated_result, rel_tol=1e-15, abs_tol=0.0)}")
print(f"scale: baseline_times_9={(9.0 * base_result)!r}; scaled={scaled_result!r}; match={math.isclose(9.0 * base_result, scaled_result, rel_tol=1e-15, abs_tol=0.0)}")
print(f"permutation: baseline={base_result!r}; reversed={permuted_result!r}; match={math.isclose(base_result, permuted_result, rel_tol=1e-15, abs_tol=0.0)}")

try:
    population_variance([])
except ValueError as error:
    print(f"empty input: raised={type(error).__name__}; match=True")
else:
    print("empty input: raised=None; match=False")
