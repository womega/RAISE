from raise_xai import RAISEExplainer


def _explainer():
    return RAISEExplainer(
        vocab_cfg={
            "min_df": 0.0,
            "max_df": 1.0,
            "max_unigrams": 50,
            "max_bigrams": 50,
            "min_df_bigram": 0.0,
        },
        mining_cfg={"min_support": 0.25, "max_len": 2},
        stats_cfg={"use_fisher": False},
    )


def test_fit_and_explain_token_sequences():
    tokens = [
        ["INFO", "worker", "ok"],
        ["INFO", "worker", "ok"],
        ["ERROR", "worker", "failed"],
        ["ERROR", "worker", "failed"],
    ]
    labels = [0, 0, 1, 1]
    explainer = _explainer().fit_from_tokens(tokens, labels)
    hits = explainer.explain_event_tokens(tokens[-1], top_k=5)
    assert 1 in hits
    assert hits[1]
    assert any("tok=ERROR" in rule["lhs_items"] for rule in hits[1])


def test_fit_transactions():
    transactions = [
        {"tok=normal", "tok=worker"},
        {"tok=normal", "tok=worker"},
        {"tok=error", "tok=worker"},
        {"tok=error", "tok=worker"},
    ]
    labels = [0, 0, 1, 1]
    explainer = _explainer().fit_transactions(transactions, labels)
    assert explainer.rules()
