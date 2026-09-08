# RAISE methodology

RAISE is a supervised descriptive rule-mining explainer operating on event-level symbolic transactions and a discrete target. A target can represent a ground-truth class, detector prediction, or a derived behaviour category such as a confusion quadrant.

## Transaction construction

The reference implementation supports three direct fitting interfaces:

- `fit_from_tokens`: tokenizer-aligned sequences;
- `fit`: raw log strings with canonicalization and optional coarse shape items;
- `fit_transactions`: already constructed symbolic transactions.

Tokenizer-first mode is the reference path for the paper because it aligns symbolic items with the detector's own representation.

## Mining

RAISE mines frequent antecedents with Apriori. For each target class it constructs class-conditional rules and computes:

- support;
- confidence / precision;
- lift;
- leverage;
- conviction;
- improvement over the class base rate;
- PMI;
- WRAcc;
- coverage;
- recall; and
- F1.

The default human-facing `score` is WRAcc.

## Statistical filtering

When enabled, RAISE performs one-sided Fisher exact tests on rule contingency tables and applies a Holm adjustment within each target class.

## Stability filtering

When enabled, RAISE re-estimates rule occurrence over bootstrap resamples and retains rules whose bootstrap frequency exceeds the configured threshold.

## Per-event explanations

Once a rule inventory is fitted, a log line is explained by retrieving rules whose antecedents are satisfied by that line and ranking them with a configured selector. Token-derived rule units can be projected back to whitespace-delimited log components.

## Interpretation boundary

RAISE is descriptive and post hoc. A rule can be faithful to detector behaviour without being semantically correct, causally complete, or an expert-valid root-cause explanation. The paper's masking diagnostics measure sensitivity/faithfulness to the detector only.
