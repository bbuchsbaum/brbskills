"""Candidate population-variance implementation for finite float observations."""

def population_variance(values):
    if not values:
        raise ValueError("at least one observation is required")
    mean = sum(values) / len(values)
    return sum(value * value for value in values) / len(values) - mean * mean
