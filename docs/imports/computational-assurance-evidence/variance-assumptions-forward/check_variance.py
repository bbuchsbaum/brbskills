"""Independent finite-float variance checks; source implementation remains read-only."""
from fractions import Fraction
import importlib.util
import math

SOURCE = "/private/tmp/brbskills-assurance-import-vcirhv5_/checkout/skills/design-computational-tests/tests/fixtures/variance.py"
spec = importlib.util.spec_from_file_location("candidate_variance", SOURCE)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)


def exact_population_variance(xs):
    """Exact rational variance of the already-rounded IEEE float observations."""
    observations = [Fraction.from_float(x) for x in xs]
    mean = sum(observations) / len(observations)
    return sum((x - mean) ** 2 for x in observations) / len(observations)


def close(actual, expected):
    expected_float = float(expected)
    return math.isclose(actual, expected_float, rel_tol=2e-15, abs_tol=1e-15)


tests = [
    ("singleton", [7.0]),
    ("ordinary_spread", [1.0, 2.0, 3.0]),
    ("ordinary_mixed_sign", [-3.0, -1.0, 2.0, 6.0]),
    ("constant", [42.0, 42.0, 42.0]),
    ("large_offset_representable_spacing", [float(2**53), float(2**53 + 2), float(2**53 + 4)]),
]

for name, xs in tests:
    expected = exact_population_variance(xs)
    actual = candidate.population_variance(xs)
    print(f"{name}: values={xs!r}")
    print(f"  exact={expected} ({float(expected)!r})")
    print(f"  candidate={actual!r}; close={close(actual, expected)}")

base = [1.0, 2.0, 3.0]
# At 2**52 the local spacing is one, so adding this offset preserves each
# input exactly and translation invariance applies to the finite float inputs.
shifted = [x + float(2**52) for x in base]
base_result = candidate.population_variance(base)
shifted_result = candidate.population_variance(shifted)
print("translation_invariance:")
print(f"  base={base!r}, shifted={shifted!r}")
print(f"  candidate_base={base_result!r}, candidate_shifted={shifted_result!r}")
print(f"  exact_base={exact_population_variance(base)}, exact_shifted={exact_population_variance(shifted)}")
print(f"  preserved={close(shifted_result, exact_population_variance(shifted))}")

try:
    candidate.population_variance([])
except ValueError as exc:
    print(f"empty_input: ValueError={str(exc)!r}")
else:
    print("empty_input: no ValueError")
