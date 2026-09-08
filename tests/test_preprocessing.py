from raise_xai.preprocessing import VocabBuilder, canonicalize


def test_canonicalize_common_log_fields():
    value = canonicalize("ERROR user@example.org from 192.168.1.2 https://example.org/x")
    assert "<email>" in value
    assert "<ip>" in value
    assert "<url>" in value


def test_vocab_builder_token_items():
    builder = VocabBuilder(
        min_df=0.0,
        max_df=1.0,
        max_unigrams=10,
        max_bigrams=10,
        min_df_bigram=0.0,
    ).fit_tokens([["alpha", "beta"], ["alpha", "gamma"]])
    assert "tok=alpha" in builder.items_from_tokens(["alpha", "beta"])
