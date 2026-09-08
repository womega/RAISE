# RAISE supplementary material

This directory preserves extended numerical evidence and methodological details that are intentionally not all reproduced in the shortened conference manuscript. It is designed to be cited directly from the paper.

## Scope

The **primary paper benchmark** is the 28-scenario cross-system evaluation formed by four detector families and seven target systems. The paper also contains a **four-scenario matched cross--intra diagnostic**. The full 4 x 7 intra-system analysis is retained here as extended evidence; it is not a second primary benchmark of the short paper.

The final comparison subset contains **up to 48 lines per scenario** (up to 12 per TP/TN/FP/FN quadrant), while per-explainer configuration selection uses a disjoint validation subset of **up to 100 lines per scenario** (up to 25 per quadrant). Sampling is diagnostic and confidence-extreme rather than random or prevalence-preserving.

RAISE mines a phase-level rule inventory from the same phase corpus it explains. The validation/final split therefore prevents configuration reuse across final samples, but does **not** constitute an independent rule-mining split. The reported masking results are faithfulness diagnostics for detector behaviour, not semantic, causal, root-cause, or expert-ground-truth validation.

## Files

- `supplementary_material.md` — human-readable extended-results narrative.
- `data/global_profiles_k2.csv` — primary cross-system profile and extended full intra-system profile at k=2.
- `data/availability.csv` — scenario-mean and pooled local non-empty output rates, kept distinct because they use different aggregation units.
- `data/native_efficiency.csv` — explanation density and runtime.
- `data/controlled_cross_intra_k2.csv` — matched regime diagnostic.
- `data/k_sweep_overall.csv` — support-conditioned budget sensitivity for k in {1,2,3,5,10}.
- `data/scenario_manifest.csv` — all 28 cross-system cells and the four controlled diagnostic cells.

## Important aggregation note

The k-sweep retains only samples/cells with at least k valid units. Consequently, the k=2 row in `k_sweep_overall.csv` is a **budget-sensitivity aggregate** and can differ from the primary k=2 profile in `global_profiles_k2.csv`. The latter is the value to cite for the paper's primary cross-explainer comparison.

## Recommended paper citation sentence

> Extended results and reproducibility artefacts are available at `https://github.com/womega/RAISE`.
