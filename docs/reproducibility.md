# Reproducibility notes

## Paper scope

The primary paper benchmark contains 28 cross-system model--target scenarios:

- 4 detector families: BERT, RoBERTa, LogAnBERT, LogBERTa;
- 7 target systems: AIT, BGL, Hades, Hadoop, HDFS, OpenStack, Thunderbird.

The paper additionally reports a controlled cross--intra diagnostic for:

- BGL--RoBERTa;
- HDFS--RoBERTa;
- Hadoop--LogBERTa;
- Thunderbird--RoBERTa.

The same cross-selected final indices are routed to the appropriate held-out intra-system fold for the controlled comparison.

## Extended material

The supplementary directory retains results that are useful for auditability but were removed from the short paper, including the complete intra-system aggregate profile.

## Detector dependency

The `raise-xai` package is model-agnostic and does not bundle trained detectors. Reproducing the exact paper numbers requires the fixed detector checkpoints, representative manifests, and comparison pipeline used in the study. Those artifacts are available upon reasonable request to the corresponding author.

## Randomness

The RAISE class accepts an explicit seed. Bootstrap stability uses a deterministic local pseudo-random generator derived from that seed.
