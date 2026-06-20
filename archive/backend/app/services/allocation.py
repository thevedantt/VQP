"""Small numeric helpers for proportionally distributing integer totals."""

from __future__ import annotations


def allocate_largest_remainder(weights: dict[str, float], total: int) -> dict[str, int]:
    """Distribute ``total`` integer units across ``weights`` proportionally.

    Uses the largest-remainder (Hamilton) method so the resulting values
    always sum to exactly ``total``, which matters both for chapter
    weightage percentages (total=100) and question-count allocations
    (total=total_questions).
    """

    keys = list(weights.keys())
    if total <= 0 or not keys:
        return {k: 0 for k in keys}

    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        weights = {k: 1.0 for k in keys}
        weight_sum = float(len(keys))

    raw = {k: (weights[k] / weight_sum) * total for k in keys}
    floors = {k: int(raw[k]) for k in keys}
    remainder = total - sum(floors.values())

    # Give the leftover units to the keys with the largest fractional parts.
    order = sorted(keys, key=lambda k: raw[k] - floors[k], reverse=True)
    for k in order[:remainder]:
        floors[k] += 1

    return floors
