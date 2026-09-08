from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_ALLOWED_TARGETS = {
    "quadrants",
    "ground_truth",
    "model_behavior",
    "predicted_label",
    "confidence_bins",
    "anomaly_score_bins",
    "cluster_id",
    "pseudo_label",
}
_ALLOWED_REDUNDANCY = {
    "max_improvement",
    "max_mi",
    "max_wracc",
    "max_precision",
    "max_coverage",
    "max_f1",
    "richest",
}
_ALLOWED_SCORE_KEYS = {
    "score",
    "wracc",
    "improvement",
    "pmi",
    "confidence",
    "precision",
    "f1",
    "coverage",
}


def validate_raise_cfg(cfg: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate and normalize a RAISE configuration mapping."""
    cfg = dict(cfg or {})
    out: dict[str, Any] = {
        "target": cfg.get("target", "quadrants"),
        "threshold": float(cfg.get("threshold", 0.5)),
        "vocab": {
            "max_unigrams": 3000,
            "min_df": 0.005,
            "max_df": 0.60,
            "max_bigrams": 500,
            "min_df_bigram": 0.003,
        },
        "mining": {
            "min_support": None,
            "max_len": 6,
            "use_stability": False,
            "bootstrap_B": 50,
            "bootstrap_keep": 0.60,
        },
        "stats": {"use_fisher": True, "alpha": 0.05},
        "itemizer": cfg.get("itemizer", "tokenizer"),
        "shape_mode": cfg.get("shape_mode", "log"),
        "redundancy": cfg.get("redundancy", "max_improvement"),
        "score_key": cfg.get("score_key", "wracc"),
        "topk_event_rules": int(cfg.get("topk_event_rules", 5)),
        "hits_batch_size": int(cfg.get("hits_batch_size", 256)),
    }
    out["vocab"].update(dict(cfg.get("vocab", {}) or {}))
    out["mining"].update(dict(cfg.get("mining", {}) or {}))
    out["stats"].update(dict(cfg.get("stats", {}) or {}))

    for key, value in cfg.items():
        if key not in out:
            out[key] = value

    if out["target"] not in _ALLOWED_TARGETS:
        raise ValueError(f"target must be one of {sorted(_ALLOWED_TARGETS)}, got {out['target']!r}")
    if out["redundancy"] not in _ALLOWED_REDUNDANCY:
        raise ValueError(
            f"redundancy must be one of {sorted(_ALLOWED_REDUNDANCY)}, got {out['redundancy']!r}"
        )
    if out["score_key"] not in _ALLOWED_SCORE_KEYS:
        raise ValueError(
            f"score_key must be one of {sorted(_ALLOWED_SCORE_KEYS)}, got {out['score_key']!r}"
        )
    if out["itemizer"] not in {"tokenizer", "regex_log", "pretokenized", "symbolic"}:
        raise ValueError("itemizer must be one of tokenizer, regex_log, pretokenized, symbolic")
    if out["shape_mode"] not in {"log", "none", "custom"}:
        raise ValueError("shape_mode must be one of log, none, custom")
    if not 0.0 <= out["threshold"] <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    if out["topk_event_rules"] <= 0 or out["hits_batch_size"] <= 0:
        raise ValueError("topk_event_rules and hits_batch_size must be positive")
    min_support = out["mining"].get("min_support")
    if min_support is not None and not 0.0 < float(min_support) <= 1.0:
        raise ValueError("mining.min_support must be in (0, 1]")
    if int(out["mining"].get("max_len", 0)) <= 0:
        raise ValueError("mining.max_len must be positive")
    if not 0.0 < float(out["stats"].get("alpha", 0.0)) <= 1.0:
        raise ValueError("stats.alpha must be in (0, 1]")
    return out
