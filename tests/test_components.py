from raise_xai import (
    aggregate_component_raise_values,
    merge_subword_tokens,
    project_raise_rule_to_components,
)


def test_wordpiece_merge():
    merged, mapping = merge_subword_tokens(["Data", "##Node", "failed"], "wordpiece")
    assert merged == ["DataNode", "failed"]
    assert mapping == [0, 0, 1]


def test_rule_projection_and_aggregation():
    sentence = "ERROR DataNode failed"
    tokens = ["ERROR", "DataNode", "failed"]
    rule = {"lhs_items": ("tok=ERROR", "tok=failed"), "score": 0.4}
    assert project_raise_rule_to_components(sentence, tokens, rule) == ["ERROR", "failed"]
    values = aggregate_component_raise_values(sentence, tokens, [rule])
    assert values["ERROR"] == 0.2
    assert values["failed"] == 0.2
