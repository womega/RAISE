from __future__ import annotations

import json
import math
import os
import random
import time
from collections import defaultdict
from pathlib import Path

try:
    from scipy.stats import fisher_exact
except ImportError:  # pragma: no cover - scipy is a declared dependency
    fisher_exact = None

from .mining import (
    apriori,
    class_base_rate,
    fisher_holm,
    rule_metrics,
)
from .preprocessing import (
    VocabBuilder,
    canonicalize,
    extract_shape_items,
)
from .scoring import (
    rule_importance_score,
    select_by_concept,
    sort_rules_by_selector,
)


class RAISEExplainer:
    """Tokenizer-aware descriptive rule-mining explainer.

    Notes
    -----
    ``fit`` and ``fit_from_tokens`` construct a shared rule inventory from the supplied
    explanation corpus. If the same samples are then explained, the evaluation is
    transductive with respect to that rule inventory. Use an independently selected corpus
    when you specifically want to study rule-inventory generalization.
    """

    def __init__(
        self,
        vocab_cfg: dict | None = None,
        mining_cfg: dict | None = None,
        stats_cfg: dict | None = None,
        redundancy: str = "max_improvement",
        seed: int = 13,
        profile: bool = False,
        sink_jsonl: str | os.PathLike[str] | None = None,
    ) -> None:
        self.profile = bool(profile)
        self.sink_jsonl = Path(sink_jsonl) if sink_jsonl is not None else None
        self.profile_: list[dict] = []
        self.vocab_cfg = {
            "max_unigrams": 3000,
            "min_df": 0.005,
            "max_df": 0.60,
            "max_bigrams": 500,
            "min_df_bigram": 0.003,
            **(vocab_cfg or {}),
        }
        self.mining_cfg = {
            "min_support": None,
            "max_len": 6,
            "use_stability": False,
            "bootstrap_B": 50,
            "bootstrap_keep": 0.60,
            **(mining_cfg or {}),
        }
        self.stats_cfg = {"use_fisher": True, "alpha": 0.05, **(stats_cfg or {})}
        self.redundancy = redundancy
        self.seed = int(seed)
        self.vocab_: VocabBuilder | None = None
        self.rules_: dict[int, list[dict]] = {}
        self.rules_selected_: dict[str, list[dict]] = {}
        self.stability_summary_: dict[str, object] = {}

    def _tick(self, phase: str, started: float, **extras: object) -> None:
        if not self.profile:
            return
        record = {"phase": phase, "duration_s": time.perf_counter() - started, **extras}
        self.profile_.append(record)
        if self.sink_jsonl is not None:
            self.sink_jsonl.parent.mkdir(parents=True, exist_ok=True)
            with self.sink_jsonl.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")

    def event_items(self, raw_line: str, *, include_shape: bool = True) -> set[str]:
        canonical = canonicalize(raw_line)
        items = extract_shape_items(canonical) if include_shape else set()
        if self.vocab_ is not None:
            items |= self.vocab_.items_from(canonical)
        return items

    def event_items_from_tokens(
        self,
        tokens: list[str],
        *,
        include_shape: bool = False,
    ) -> set[str]:
        items = extract_shape_items(" ".join(tokens)) if include_shape else set()
        if self.vocab_ is not None:
            items |= self.vocab_.items_from_tokens(tokens)
        return items

    @staticmethod
    def _validate_fit_input(items: list, labels: list[int]) -> None:
        if len(items) != len(labels):
            raise ValueError("items and labels must have the same length")
        if not items:
            raise ValueError("at least one explanation sample is required")

    @staticmethod
    def _rhs_event_set(labels: list[int], cls: int) -> set[int]:
        return {index for index, value in enumerate(labels) if value == cls}

    def _build_rules(
        self,
        transactions: list[set[str]],
        labels: list[int],
        classes: list[int],
        min_support: float,
    ) -> dict[int, list[dict]]:
        n = len(transactions)
        frequent = apriori(
            transactions,
            min_support=min_support,
            max_len=int(self.mining_cfg["max_len"]),
        )
        rhs_counts = {cls: sum(value == cls for value in labels) for cls in classes}
        base_rates = {cls: class_base_rate(labels, cls) for cls in classes}
        all_rules: dict[int, list[dict]] = {cls: [] for cls in classes}

        inverted: dict[str, set[int]] = defaultdict(set)
        for index, transaction in enumerate(transactions):
            for item in transaction:
                inverted[item].add(index)
        rhs_events = {cls: self._rhs_event_set(labels, cls) for cls in classes}

        def events_for_itemset(lhs: frozenset[str]) -> set[int]:
            values = list(lhs)
            if not values:
                return set()
            events = inverted[values[0]].copy()
            for item in values[1:]:
                events &= inverted[item]
            return events

        for itemsets in frequent.values():
            for cls in classes:
                for lhs in itemsets:
                    lhs_events = events_for_itemset(lhs)
                    n_lhs = len(lhs_events)
                    n_rhs = rhs_counts[cls]
                    if not n_lhs or not n_rhs:
                        continue
                    n_both = len(lhs_events & rhs_events[cls])
                    if n_both / n < min_support:
                        continue

                    support, confidence, lift, leverage, conviction = rule_metrics(
                        n, n_lhs, n_rhs, n_both
                    )
                    improvement = confidence - base_rates[cls]
                    p_ab = n_both / n
                    p_a = n_lhs / n
                    p_b = n_rhs / n
                    pmi = math.log2((p_ab + 1e-12) / (p_a * p_b + 1e-12))
                    recall = n_both / n_rhs if n_rhs else 0.0
                    f1 = (
                        2 * confidence * recall / (confidence + recall)
                        if confidence + recall
                        else 0.0
                    )
                    p_value = None
                    if bool(self.stats_cfg.get("use_fisher", True)) and fisher_exact is not None:
                        table = [
                            [n_both, n_lhs - n_both],
                            [n_rhs - n_both, n - n_lhs - n_rhs + n_both],
                        ]
                        _, p_value = fisher_exact(table, alternative="greater")

                    rule = {
                        "lhs_items": tuple(sorted(lhs)),
                        "rhs_class": cls,
                        "support": support,
                        "confidence": confidence,
                        "lift": lift,
                        "leverage": leverage,
                        "conviction": conviction,
                        "improvement": improvement,
                        "pmi": pmi,
                        "count_lhs": n_lhs,
                        "count_rhs": n_rhs,
                        "count_both": n_both,
                        "p_value": p_value,
                        "coverage": n_lhs / n,
                        "precision": confidence,
                        "wracc": (n_lhs / n) * improvement,
                        "recall": recall,
                        "f1": f1,
                    }
                    rule["score"] = rule_importance_score(rule)
                    all_rules[cls].append(rule)

        alpha = float(self.stats_cfg.get("alpha", 0.05))
        for cls in classes:
            pvalues = [rule["p_value"] for rule in all_rules[cls] if rule["p_value"] is not None]
            if pvalues and fisher_exact is not None:
                adjusted = fisher_holm(pvalues)
                cursor = 0
                for rule in all_rules[cls]:
                    if rule["p_value"] is None:
                        rule["p_adj"] = None
                    else:
                        rule["p_adj"] = adjusted[cursor]
                        cursor += 1
                all_rules[cls] = [
                    rule
                    for rule in all_rules[cls]
                    if rule["p_adj"] is not None and rule["p_adj"] < alpha
                ]
            else:
                for rule in all_rules[cls]:
                    rule["p_adj"] = None
        return all_rules

    def _resolved_min_support(self, n: int) -> float:
        configured = self.mining_cfg.get("min_support")
        if configured is not None:
            return float(configured)
        return max(0.001, math.ceil(10 / n) / n)

    def _apply_stability_gate(
        self,
        transactions: list[set[str]],
        labels: list[int],
        classes: list[int],
        min_support: float,
        rules: dict[int, list[dict]],
    ) -> dict[int, list[dict]]:
        if not bool(self.mining_cfg.get("use_stability", False)):
            self.stability_summary_ = {"enabled": False}
            return rules

        n = len(transactions)
        bootstraps = max(1, int(self.mining_cfg.get("bootstrap_B", 50)))
        keep_threshold = float(self.mining_cfg.get("bootstrap_keep", 0.60))
        counts: dict[tuple[tuple[str, ...], int], int] = defaultdict(int)
        rng = random.Random(self.seed)

        for _ in range(bootstraps):
            ids = [rng.randrange(n) for _ in range(n)]
            tx_sample = [transactions[index] for index in ids]
            y_sample = [labels[index] for index in ids]
            sampled_rules = self._build_rules(tx_sample, y_sample, classes, min_support=min_support)
            seen = {
                (tuple(rule["lhs_items"]), int(cls))
                for cls, class_rules in sampled_rules.items()
                for rule in class_rules
            }
            for pair in seen:
                counts[pair] += 1

        kept: dict[int, list[dict]] = {cls: [] for cls in classes}
        before = sum(len(values) for values in rules.values())
        for cls, class_rules in rules.items():
            for rule in class_rules:
                pair = (tuple(rule["lhs_items"]), int(cls))
                frequency = counts.get(pair, 0) / bootstraps
                row = dict(rule)
                row["stability"] = frequency
                row["stability_kept"] = frequency >= keep_threshold
                if row["stability_kept"]:
                    kept[cls].append(row)
        self.stability_summary_ = {
            "enabled": True,
            "bootstrap_B": bootstraps,
            "bootstrap_keep": keep_threshold,
            "n_rules_before": before,
            "n_rules_after": sum(len(values) for values in kept.values()),
        }
        return kept

    def _finalize_fit(
        self,
        transactions: list[set[str]],
        labels: list[int],
        classes: list[int],
    ) -> None:
        min_support = self._resolved_min_support(len(transactions))
        rules = self._build_rules(transactions, labels, classes, min_support)
        self.rules_ = self._apply_stability_gate(transactions, labels, classes, min_support, rules)
        selectors = (
            "max_improvement",
            "max_mi",
            "max_wracc",
            "max_precision",
            "max_coverage",
            "max_f1",
            "richest",
        )
        self.rules_selected_ = {
            selector: select_by_concept(self.rules_, selector) for selector in selectors
        }

    def fit_transactions(
        self,
        transactions: list[set[str]],
        labels: list[int],
        classes: list[int] | None = None,
    ) -> RAISEExplainer:
        self._validate_fit_input(transactions, labels)
        resolved_classes = classes or sorted(set(labels))
        self._finalize_fit(transactions, labels, resolved_classes)
        return self

    def fit_from_tokens(
        self,
        token_seqs: list[list[str]],
        labels: list[int],
        classes: list[int] | None = None,
        *,
        include_shape: bool = False,
    ) -> RAISEExplainer:
        self._validate_fit_input(token_seqs, labels)
        resolved_classes = classes or sorted(set(labels))
        started = time.perf_counter()
        self.vocab_ = VocabBuilder(**self.vocab_cfg).fit_tokens(token_seqs)
        self._tick("raise.fit.vocab_tokens", started, n_events=len(token_seqs))
        started = time.perf_counter()
        transactions = [
            self.event_items_from_tokens(seq, include_shape=include_shape) for seq in token_seqs
        ]
        self._tick(
            "raise.fit.transactions_tokens",
            started,
            avg_items=sum(map(len, transactions)) / len(transactions),
        )
        started = time.perf_counter()
        self._finalize_fit(transactions, labels, resolved_classes)
        self._tick(
            "raise.fit.rules_stats_tokens",
            started,
            n_rules_sum=sum(map(len, self.rules_.values())),
        )
        return self

    def fit(
        self,
        logs: list[str],
        labels: list[int],
        classes: list[int] | None = None,
        *,
        shape_mode: str = "log",
    ) -> RAISEExplainer:
        self._validate_fit_input(logs, labels)
        resolved_classes = classes or sorted(set(labels))
        canonical = [canonicalize(line) for line in logs]
        started = time.perf_counter()
        self.vocab_ = VocabBuilder(**self.vocab_cfg).fit(canonical)
        self._tick(
            "raise.fit.vocab",
            started,
            n_unigrams=len(self.vocab_.unigrams_),
            n_bigrams=len(self.vocab_.bigrams_),
        )
        include_shape = shape_mode != "none"
        transactions = [
            (extract_shape_items(line) if include_shape else set()) | self.vocab_.items_from(line)
            for line in canonical
        ]
        self._finalize_fit(transactions, labels, resolved_classes)
        return self

    def _rank_hits(self, hits: list[dict]) -> list[dict]:
        return sort_rules_by_selector(hits, self.redundancy)

    def explain_event_tokens(
        self,
        tokens: list[str],
        *,
        top_k: int = 5,
    ) -> dict[int, list[dict]]:
        items = self.event_items_from_tokens(tokens)
        return {
            cls: self._rank_hits(
                [rule for rule in rules if set(rule["lhs_items"]).issubset(items)]
            )[:top_k]
            for cls, rules in self.rules_.items()
        }

    def explain_event(
        self,
        raw_line: str,
        *,
        top_k: int = 5,
    ) -> dict[int, list[dict]]:
        items = self.event_items(raw_line)
        return {
            cls: self._rank_hits(
                [rule for rule in rules if set(rule["lhs_items"]).issubset(items)]
            )[:top_k]
            for cls, rules in self.rules_.items()
        }

    def rules(self, selector: str | None = None) -> list[dict]:
        """Return the global rule inventory or one representative selector view."""
        if selector is None:
            return [rule for rules in self.rules_.values() for rule in rules]
        return list(self.rules_selected_.get(selector, []))
