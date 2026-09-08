# Unified cross-explainer evaluation protocol

The RAISE paper treats explainer comparison as a first-class methodological problem because sparse symbolic and dense attribution explainers have structurally different outputs.

## Two-phase design

### 1. Native configuration selection

Each explainer is configured on a validation subset using its own native controls. Final-comparison indices are excluded before the validation subset is formed.

### 2. Shared-budget final comparison

Selected configurations are frozen and evaluated on a disjoint final subset under the same evidence-unit and masking semantics.

The paper uses:

- up to 100 validation lines per scenario, up to 25 per TP/TN/FP/FN quadrant;
- up to 48 final lines per scenario, up to 12 per quadrant;
- confidence-extreme diagnostic sampling;
- primary shared inspection budget `k=2`.

The 48-line figure is a nominal maximum. It is not a natural-distribution sample size.

## Ranking

- SHAP: absolute attribution magnitude;
- LIME: absolute local coefficient magnitude;
- Anchors: clause order;
- RAISE: fixed support-first signed rule semantics in the shared comparison layer.

Keep/Remove tests use cumulative ranked prefixes. They do not enumerate arbitrary feature subsets and do not establish globally optimal subsets or exhaustive interactions.

## Empty outputs

Empty explanations remain outcomes. Two overlap summaries are therefore distinct:

- **overall agreement**: empty selections contribute zero overlap;
- **shared-output agreement**: computed only when both explainers produce non-empty selections.

## Faithfulness

For the original predicted class `j`:

- comprehensiveness compares original confidence against confidence after removing selected units;
- sufficiency compares original confidence against confidence when only selected units are retained.

Flip, Damage, and Fix metrics distinguish label changes from prediction correctness. A Fix after masking does not prove semantic correctness.

## RAISE rule-inventory scope

The paper-level RAISE inventory is phase-level: the final comparison lines participate in the inventory used to explain that phase. Validation and final subsets are disjoint for configuration selection, but there is no independent rule-mining split. This is a transductive explanation evaluation, not a rule-inventory generalization claim.
