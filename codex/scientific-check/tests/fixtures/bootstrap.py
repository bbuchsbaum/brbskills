"""Percentile interval for the population mean response from repeated readings."""
import random

def confidence_interval(rows, seed=2026, replicates=999):
    rng = random.Random(seed)
    values = [float(row["response"]) for row in rows]
    estimates = sorted(sum(rng.choices(values, k=len(values))) / len(values)
                       for _ in range(replicates))
    return estimates[int(0.025 * replicates)], estimates[int(0.975 * replicates)]
