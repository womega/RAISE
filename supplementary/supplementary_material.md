# Supplementary Material: RAISE

## S1. Evaluation scope and fairness controls

The paper compares sparse symbolic and dense attribution explainers under a common analyst-facing inspection budget while preserving explainer-native configuration selection. Empty outputs remain first-class outcomes. Overall pairwise agreement therefore counts empty selections as zero overlap, while shared-output agreement conditions on both explainers returning non-empty evidence.

The primary benchmark consists of 28 cross-system model--dataset scenarios. Each scenario uses up to 100 validation lines for explainer configuration selection and a disjoint final subset of up to 48 lines for comparison. The final subset is stratified by TP/TN/FP/FN and intentionally confidence-extreme. It should not be interpreted as an estimate under the target system's natural prevalence or error distribution.

RAISE's rule inventory is phase-level and transductive with respect to the corpus supplied to the explainer. A future rule-inventory generalization study should mine the inventory on an independent corpus before explaining held-out samples.

## S2. Primary cross-system profile at k=2

| Explainer | Comprehensiveness ↑ | Sufficiency ↓ | Keep Damage ↓ | Remove Damage ↑ | Remove Fix ↓ | Local availability |
|---|---:|---:|---:|---:|---:|---:|
| RAISE | 0.076 ± 0.105 | 0.346 ± 0.219 | 0.151 ± 0.140 | 0.036 ± 0.087 | **0.047 ± 0.092** | 99.4% |
| Anchors | 0.154 ± 0.149 | **0.155 ± 0.194** | **0.148 ± 0.249** | **0.153 ± 0.252** | 0.213 ± 0.284 | 47.5% |
| SHAP | 0.124 ± 0.176 | 0.508 ± 0.204 | 0.268 ± 0.110 | 0.054 ± 0.100 | 0.082 ± 0.124 | 100.0% |
| LIME | **0.264 ± 0.193** | 0.265 ± 0.235 | **0.148 ± 0.155** | 0.119 ± 0.098 | 0.159 ± 0.133 | 100.0% |

These results support complementary explanatory profiles rather than a universal ranking. Anchors' favourable perturbation values are conditional on substantially lower output availability. RAISE is compact, efficient, and highly available, but it does not lead comprehensiveness in the primary cross-system profile.

The 47.5% Anchors figure above is the paper's **scenario-mean local availability**. The support table also reports a **pooled sample non-empty rate** of 45.7%. These are different aggregation units and are intentionally preserved separately in `data/availability.csv`; they should not be treated as conflicting estimates.

## S3. Full intra-system profile retained outside the short paper

| Explainer | Comprehensiveness ↑ | Sufficiency ↓ | Keep Damage ↓ | Remove Damage ↑ | Remove Fix ↓ |
|---|---:|---:|---:|---:|---:|
| RAISE | **0.475 ± 0.110** | 0.487 ± 0.082 | **0.156 ± 0.089** | 0.082 ± 0.088 | 0.396 ± 0.130 |
| Anchors | 0.268 ± 0.154 | 0.233 ± 0.159 | 0.196 ± 0.345 | 0.017 ± 0.038 | 0.559 ± 0.237 |
| SHAP | 0.064 ± 0.103 | 0.475 ± 0.100 | 0.443 ± 0.135 | 0.061 ± 0.094 | **0.012 ± 0.053** |
| LIME | 0.357 ± 0.129 | **0.209 ± 0.143** | 0.201 ± 0.151 | **0.338 ± 0.141** | 0.020 ± 0.057 |

This full intra-system analysis is extended supplementary evidence. The conference paper uses only the controlled four-scenario matched cross--intra diagnostic to isolate detector-regime effects while holding sample identity fixed.

## S4. Native explanation density and runtime

| Explainer | Native units ↓ | Seconds/sample ↓ |
|---|---:|---:|
| RAISE | 3.399 ± 0.747 | **0.326 ± 0.771** |
| Anchors | **2.594 ± 2.565** | 381.910 ± 691.678 |
| SHAP | 86.835 ± 45.774 | 0.806 ± 0.393 |
| LIME | 16.558 ± 9.110 | 1.956 ± 1.091 |

Compactness and runtime favour RAISE as a practical symbolic complement. They should not be read as proof of superior faithfulness.

## S5. Controlled cross--intra diagnostic

The controlled diagnostic reuses the same cross-selected final indices in four representative scenarios: BGL--RoBERTa, HDFS--RoBERTa, Hadoop--LogBERTa, and Thunderbird--RoBERTa. Each intra-system sample is routed to the fold-specific held-out model.

| Explainer | Cross C. ↑ | Intra C. ↑ | Δ C. | Cross S. ↓ | Intra S. ↓ | Δ S. | Δ Keep Flip ↓ | Δ Remove Flip ↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RAISE | -0.039 | 0.064 | +0.103 | -0.388 | 0.093 | +0.481 | -0.185 | +0.017 |
| LIME | -0.036 | 0.141 | +0.177 | -0.172 | -0.007 | +0.166 | -0.099 | -0.078 |
| SHAP | -0.190 | 0.097 | +0.286 | -0.009 | 0.101 | +0.110 | -0.005 | -0.125 |

The joint increase in comprehensiveness and sufficiency shows why the intra-regime explanations cannot simply be labelled “better”: the same regime shift can increase remove-side disruption while weakening keep-only preservation.

## S6. Budget sensitivity

`data/k_sweep_overall.csv` records the exact support-conditioned aggregate values for k ∈ {1,2,3,5,10}. Sparse explainers lose support as k increases because only samples with at least k valid units contribute. The sweep is therefore a ranked-prefix sensitivity analysis, not an exhaustive feature-interaction search and not a global-optimality test.

The primary paper comparison remains k=2 in `data/global_profiles_k2.csv`.

## S7. Interpretation limits

The study contains no expert annotation of semantically or causally correct explanatory units. Qualitative examples illustrate readability and structural differences between explanation families, but are not human-grounded validation. Likewise, masking-based Keep/Remove metrics diagnose faithfulness to each fixed detector's behaviour, including its errors; they do not establish that the detector decision itself is correct.

## S8. Reproducibility map

The installable `raise_xai` package in this repository contains the RAISE algorithm. The paper-level comparison additionally depends on the fixed transformer detectors and the SHAP, LIME, and Anchors comparison implementations. The repository separates algorithm code from paper/supplementary evidence so that installing RAISE does not require the full experimental framework.
