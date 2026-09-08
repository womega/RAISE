"""RAISE: tokenizer-aware rule-based explanations for discrete model behaviour."""

from .__about__ import __version__
from .components import (
    aggregate_component_raise_values,
    canonicalize_component_rules,
    merge_subword_tokens,
    project_raise_rule_to_component_indices,
    project_raise_rule_to_components,
    readable_lhs_items,
)
from .config import validate_raise_cfg
from .core import RAISEExplainer

__all__ = [
    "__version__",
    "RAISEExplainer",
    "validate_raise_cfg",
    "aggregate_component_raise_values",
    "canonicalize_component_rules",
    "merge_subword_tokens",
    "project_raise_rule_to_component_indices",
    "project_raise_rule_to_components",
    "readable_lhs_items",
]
