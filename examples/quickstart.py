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

for target, rules in explainer.explain_event_tokens(token_sequences[-1], top_k=3).items():
    print(f"target={target}")
    for rule in rules:
        print(
            f"  {rule['lhs_items']} wracc={rule['wracc']:.3f} confidence={rule['confidence']:.3f}"
        )
