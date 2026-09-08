# RAISE

**RAISE (Rule-based Antecedent Inference for Symbolic Evidence)** is a tokenizer-aware, model-agnostic rule-based explainer for discrete model behaviour. It converts raw or tokenizer-aligned inputs into symbolic transactions, mines frequent antecedents, scores class-conditional rules with established rule-interestingness measures, and maps rule evidence back to human-readable input components.

This repository is the reference implementation and supplementary-material home for:

> **RAISE: Tokenizer-Aware Rule-Based Explanations for Transformer Log Anomaly Detection**  
> Paul K. Mvula, Paula Branco, Guy-Vincent Jourdan, Iosif-Viorel Onut, and Herna L. Viktor.

The paper evaluates RAISE within a unified comparison protocol for sparse symbolic and dense attribution explainers across transformer-based log anomaly detectors.

## What RAISE provides

RAISE supports:

- tokenizer-first explanations aligned with a model's tokenization;
- raw-log canonicalization for regex/log-oriented use;
- unigram and bigram symbolic transaction construction;
- Apriori frequent-itemset mining;
- rule scores including support, confidence, lift, leverage, improvement, PMI, WRAcc, precision, coverage, recall, and F1;
- optional one-sided Fisher tests with Holm adjustment;
- optional bootstrap stability filtering;
- per-event rule retrieval;
- projection from symbolic token rules to readable log components; and
- exportable global rule inventories for auditing and downstream analysis.

RAISE is a **descriptive post-hoc explainer**. Masking-based tests used in the paper evaluate faithfulness to detector behaviour; they do not establish expert, semantic, causal, or root-cause correctness.

## Installation

### PyPI

Once a release is published:

```bash
pip install raise-xai
```

### From source

```bash
git clone https://github.com/womega/RAISE.git
cd RAISE
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For conventional requirements-file workflows, the repository also provides:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

The package metadata and dependency declarations in `pyproject.toml` remain authoritative; the requirements files are convenience mirrors for source checkouts.

A `Makefile` is provided for the common development workflow:

```bash
make venv
source .venv/bin/activate
make ci
```

`make ci` is self-contained: it installs the checkout in editable mode with the development extras before linting, formatting checks, tests, and package build. This matters because RAISE uses a `src/` package layout, which is intentionally not importable from a clean checkout until installed. Run `make help` to list all available targets.

## Quick start: tokenizer-aligned input

```python
from raise_xai import RAISEExplainer

token_sequences = [
    ["INFO", "DataNode", "block", "received"],
    ["INFO", "DataNode", "block", "received"],
    ["ERROR", "DataNode", "block", "failed"],
    ["ERROR", "DataNode", "block", "failed"],
]
targets = [0, 0, 1, 1]

explainer = RAISEExplainer(
    vocab_cfg={"min_df": 0.0, "max_df": 1.0, "min_df_bigram": 0.0},
    mining_cfg={"min_support": 0.25, "max_len": 2},
    stats_cfg={"use_fisher": False},
).fit_from_tokens(token_sequences, targets)

hits = explainer.explain_event_tokens(
    ["ERROR", "DataNode", "block", "failed"],
    top_k=3,
)

for target_class, rules in hits.items():
    print(target_class)
    for rule in rules:
        print(rule["lhs_items"], rule["wracc"], rule["confidence"])
```

## Quick start: raw logs

```python
from raise_xai import RAISEExplainer

logs = [
    "INFO service worker completed request",
    "INFO service worker completed request",
    "ERROR service worker failed request",
    "ERROR service worker failed request",
]
targets = [0, 0, 1, 1]

explainer = RAISEExplainer(
    vocab_cfg={"min_df": 0.0, "max_df": 1.0, "min_df_bigram": 0.0},
    mining_cfg={"min_support": 0.25, "max_len": 2},
    stats_cfg={"use_fisher": False},
).fit(logs, targets, shape_mode="none")

print(explainer.explain_event("ERROR service worker failed request", top_k=3))
```

## Component-level projection

```python
from raise_xai import aggregate_component_raise_values

sentence = "ERROR DataNode block failed"
tokens = ["ERROR", "DataNode", "block", "failed"]

rules = explainer.explain_event_tokens(tokens, top_k=3)[1]
component_scores = aggregate_component_raise_values(
    sentence,
    tokens,
    rules,
    weight_key="wracc",
)
print(component_scores)
```

## Important evaluation semantics

The paper's comparison protocol separates two ideas that should not be conflated:

1. **Native configuration selection**: each explainer is tuned according to its own output structure and configuration semantics.
2. **Shared-budget comparison**: selected configurations are frozen and compared under a common low inspection budget with identical masking and evidence-unit conventions.

Empty explanations are retained as outcomes. Pairwise agreement is reported both overall and conditional on both explainers returning non-empty outputs.

### Phase-level rule inventory

RAISE builds a shared rule inventory from the corpus supplied to `fit`, `fit_from_tokens`, or `fit_transactions`. If those same samples are then explained, the explanation analysis is transductive with respect to the rule inventory. For an independent rule-inventory generalization study, fit RAISE on a separate corpus and explain held-out samples afterwards.

## Repository layout

```text
src/raise_xai/       installable Python package
tests/               unit and smoke tests
examples/            runnable examples
docs/                method, protocol, reproducibility, and release notes
supplementary/       extended results omitted from the short paper
.github/             CI, PyPI release workflow, and Dependabot
Makefile             local development/CI command entry points
requirements*.txt    conventional runtime/development dependency mirrors
```

## Reproducing the paper-level comparison

RAISE itself is detector-agnostic. The paper-level experiments additionally require the fixed trained transformer detectors and the comparison implementations for SHAP, LIME, and Anchors. The supplementary directory records the comparison scope and extended results retained outside the 12-page manuscript. See:

- `docs/methodology.md`
- `docs/evaluation-protocol.md`
- `docs/reproducibility.md`
- `supplementary/README.md`

## Development

The shortest full local validation workflow is:

```bash
make ci
```

`make ci` first performs an editable development install and then runs linting, formatting checks, tests, and a package build. If the development environment is already installed and you only want the checks, use:

```bash
make check
```

The equivalent direct commands remain supported:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m build
```

## Citation

Use `CITATION.cff` for citation metadata. The reference paper is the preferred scientific citation for the method.

## License

RAISE is distributed under the MIT License. See `LICENSE`.
