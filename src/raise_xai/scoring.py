from __future__ import annotations

from collections import defaultdict


def rule_importance_score(rule: dict) -> float:
    """Return the default human-facing rule weight (WRAcc when available)."""
    if rule.get("wracc") is not None:
        return float(rule["wracc"])
    return float(rule.get("coverage", 0.0)) * float(rule.get("improvement", 0.0))


def sort_rules_by_selector(rules: list[dict], selector: str) -> list[dict]:
    if selector == "max_improvement":

        def key(rule):
            return (rule["improvement"], rule["confidence"], rule["lift"])

    elif selector == "max_mi":

        def key(rule):
            return (rule["pmi"], rule["confidence"])

    elif selector == "max_wracc":

        def key(rule):
            return (rule.get("wracc", 0.0), rule["confidence"], rule["lift"])

    elif selector == "max_precision":

        def key(rule):
            return (rule.get("precision", 0.0), rule.get("coverage", 0.0))

    elif selector == "max_coverage":

        def key(rule):
            return (rule.get("coverage", 0.0), rule["confidence"])

    elif selector == "max_f1":

        def key(rule):
            return (
                rule.get("f1", 0.0),
                rule.get("precision", 0.0),
                rule.get("recall", 0.0),
            )

    else:

        def key(rule):
            return (len(rule["lhs_items"]), rule["confidence"], rule["lift"])

    return sorted(rules, key=key, reverse=True)


def concept_of_item(item: str) -> str | None:
    if item.startswith(("tok=", "ng=", "cluster=")):
        return item
    if item.startswith(
        (
            "len=",
            "entropy=",
            "digit_ratio=",
            "upper_ratio=",
            "symbol_ratio=",
            "has_json=",
            "has_kv=",
            "has_stack=",
            "has_ip=",
            "has_path=",
            "has_url=",
            "hour=",
            "dow=",
        )
    ):
        return item
    return None


def select_by_concept(rules_by_class: dict[int, list[dict]], selector: str) -> list[dict]:
    buckets: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for cls, rules in rules_by_class.items():
        for rule in rules:
            concept = next(
                (value for value in map(concept_of_item, rule["lhs_items"]) if value),
                None,
            )
            if concept is not None:
                buckets[(cls, concept)].append(rule)

    selected: list[dict] = []
    for (_cls, concept), rules in buckets.items():
        best = dict(sort_rules_by_selector(rules, selector)[0])
        best["concept"] = concept
        best["selector"] = selector
        selected.append(best)
    return selected
