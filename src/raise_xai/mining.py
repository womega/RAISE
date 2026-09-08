from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def apriori(
    transactions: list[set[str]],
    min_support: float,
    max_len: int,
) -> dict[int, dict[frozenset[str], int]]:
    """Mine frequent itemsets using a compact Apriori implementation."""
    if not transactions:
        return {}
    n = len(transactions)
    counts = Counter()
    for transaction in transactions:
        counts.update(transaction)
    level = {
        frozenset((item,)): count for item, count in counts.items() if count / n >= min_support
    }
    frequent: dict[int, dict[frozenset[str], int]] = {1: level}
    k = 2
    while k <= max_len and frequent.get(k - 1):
        previous = list(frequent[k - 1])
        candidates: set[frozenset[str]] = set()
        for i, left in enumerate(previous):
            for right in previous[i + 1 :]:
                union = left | right
                if len(union) == k and all((union - {item}) in frequent[k - 1] for item in union):
                    candidates.add(union)
        candidate_counts = Counter()
        for transaction in transactions:
            for candidate in candidates:
                if candidate.issubset(transaction):
                    candidate_counts[candidate] += 1
        level = {
            itemset: count
            for itemset, count in candidate_counts.items()
            if count / n >= min_support
        }
        if not level:
            break
        frequent[k] = level
        k += 1
    return frequent


def class_base_rate(labels: Iterable[int], cls: int) -> float:
    values = list(labels)
    return sum(value == cls for value in values) / len(values) if values else 0.0


def rule_metrics(n: int, n_lhs: int, n_rhs: int, n_both: int) -> tuple[float, ...]:
    support = n_both / n
    confidence = n_both / n_lhs if n_lhs else 0.0
    lift = confidence / (n_rhs / n) if n_rhs else 0.0
    leverage = support - (n_lhs / n) * (n_rhs / n)
    denominator = (n_lhs - n_both) / n
    p_not_rhs = 1 - (n_rhs / n)
    conviction = ((n_lhs / n) * p_not_rhs / denominator) if denominator > 0 else float("inf")
    return support, confidence, lift, leverage, conviction


def fisher_holm(pvalues: list[float]) -> list[float]:
    """Holm step-down family-wise-error adjustment."""
    m = len(pvalues)
    order = sorted(range(m), key=pvalues.__getitem__)
    adjusted = [0.0] * m
    previous = 0.0
    for rank, index in enumerate(order):
        value = max((m - rank) * pvalues[index], previous)
        adjusted[index] = min(value, 1.0)
        previous = adjusted[index]
    return adjusted
