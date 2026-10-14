import math
from statistics import mean


def summarize(values):
    if not isinstance(values, list) or not values:
        raise ValueError("expected a nonempty array of finite numbers")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in values):
        raise ValueError("expected a nonempty array of finite numbers")
    return {"count": len(values), "mean": mean(values)}
