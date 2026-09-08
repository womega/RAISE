from __future__ import annotations

from collections.abc import Iterable

_SPECIAL_TOKENS = {"[CLS]", "[SEP]", "[PAD]", "[MASK]", "<s>", "</s>", "<pad>", "<mask>"}


def detect_tokenizer_type(tokens: list[str]) -> str:
    if any(token.startswith(("Ġ", "▁")) for token in tokens):
        return "byte_bpe"
    if any(token.startswith("##") for token in tokens):
        return "wordpiece"
    return "unknown"


def merge_subword_tokens(
    tokens: list[str],
    tokenizer_type: str | None = None,
) -> tuple[list[str], list[int | None]]:
    """Merge WordPiece/BPE subwords and return token-to-merged-unit indices."""
    tokenizer_type = tokenizer_type or detect_tokenizer_type(tokens)
    merged: list[str] = []
    mapping: list[int | None] = []

    for token in tokens:
        if token in _SPECIAL_TOKENS:
            merged.append(token)
            mapping.append(len(merged) - 1)
            continue
        clean = token
        starts_new = True
        if tokenizer_type == "byte_bpe":
            if token.startswith(("Ġ", "▁")):
                clean = token[1:]
            else:
                starts_new = False
        elif tokenizer_type == "wordpiece" and token.startswith("##"):
            clean = token[2:]
            starts_new = False

        if not merged or starts_new:
            merged.append(clean or token)
        else:
            merged[-1] += clean or token
        mapping.append(len(merged) - 1)
    return merged, mapping


def normalize_raise_rule(rule: dict) -> dict:
    lhs = rule.get("lhs_items", rule.get("lhs_raw", rule.get("lhs", [])))
    if isinstance(lhs, tuple):
        lhs = list(lhs)
    lhs = [str(item) for item in (lhs or [])]
    indices = rule.get("lhs_idx")
    if isinstance(indices, list) and len(indices) == len(lhs):
        indices = [list(map(int, idx or [])) for idx in indices]
    else:
        indices = None
    result = dict(rule)
    result["lhs_raw"] = lhs
    result["lhs_idx"] = indices
    return result


def readable_lhs_items(
    lhs_items: Iterable[str],
    tokens: list[str] | None,
    lhs_idx: list[list[int]] | None = None,
) -> list[str]:
    """Translate symbolic tokenizer items into readable merged units where possible."""
    items = [str(item) for item in lhs_items]
    if tokens is None:
        return items
    merged, token_to_merged = merge_subword_tokens(tokens)
    readable: list[str] = []
    for pos, item in enumerate(items):
        explicit = lhs_idx[pos] if lhs_idx is not None and pos < len(lhs_idx) else []
        merged_ids = []
        for token_idx in explicit:
            if 0 <= token_idx < len(token_to_merged):
                merged_idx = token_to_merged[token_idx]
                if merged_idx is not None and merged_idx not in merged_ids:
                    merged_ids.append(merged_idx)
        if merged_ids:
            readable.append(" ".join(merged[index] for index in merged_ids))
            continue

        if item.startswith("tok="):
            raw = item[4:]
            matches = [
                token_to_merged[i]
                for i, token in enumerate(tokens)
                if token == raw and token_to_merged[i] is not None
            ]
            unique = list(dict.fromkeys(matches))
            readable.append(" | ".join(merged[index] for index in unique) if unique else raw)
        elif item.startswith("ng=") and "_" in item[3:]:
            left, right = item[3:].split("_", 1)
            span = None
            for i in range(len(tokens) - 1):
                if tokens[i] == left and tokens[i + 1] == right:
                    a, b = token_to_merged[i], token_to_merged[i + 1]
                    if a is not None and b is not None:
                        span = merged[a] if a == b else f"{merged[a]} {merged[b]}"
                        break
            readable.append(span or item[3:].replace("_", " "))
        else:
            readable.append(item)
    return readable


def _display_components(sentence: str) -> tuple[list[str], list[str]]:
    display = " ".join(str(sentence or "").strip().split()).split()
    return display, [part.lower() for part in display]


def _normalized_token(token: str) -> str:
    value = token.strip()
    for prefix in ("##", "Ġ", "▁"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value.lower()


def _map_tokens_to_components(tokens: list[str], components: list[str]) -> list[int | None]:
    normalized = [_normalized_token(token) for token in tokens]
    needs = [len(component) for component in components]
    mapping: list[int | None] = [None] * len(tokens)
    component_index = 0
    filled = 0
    for token_index, token in enumerate(normalized):
        if not token:
            continue
        if component_index >= len(needs):
            break
        mapping[token_index] = component_index
        filled += len(token)
        if filled >= needs[component_index]:
            component_index += 1
            filled = 0
    return mapping


def _lhs_token_indices(lhs_items: Iterable[str], tokens: list[str]) -> set[int]:
    normalized = [_normalized_token(token) for token in tokens]
    touched: set[int] = set()
    for item in map(str, lhs_items):
        if item.startswith("tok="):
            value = _normalized_token(item[4:])
            touched.update(i for i, token in enumerate(normalized) if token == value)
        elif item.startswith("ng=") and "_" in item[3:]:
            left, right = item[3:].split("_", 1)
            left, right = _normalized_token(left), _normalized_token(right)
            for i in range(len(normalized) - 1):
                if normalized[i] == left and normalized[i + 1] == right:
                    touched.update((i, i + 1))
    return touched


def project_raise_rule_to_component_indices(
    sentence: str,
    tokenized_text: list[str] | None,
    rule: dict,
) -> list[int]:
    """Project one symbolic rule onto whitespace-delimited log components."""
    _, normalized_components = _display_components(sentence)
    if not normalized_components:
        return []
    normalized_rule = normalize_raise_rule(rule)
    lhs_items = normalized_rule["lhs_raw"]

    if tokenized_text is None:
        tokens = normalized_components
        token_to_component: list[int | None] = list(range(len(tokens)))
    else:
        tokens = tokenized_text
        token_to_component = _map_tokens_to_components(tokens, normalized_components)

    explicit = normalized_rule.get("lhs_idx")
    if tokenized_text is not None and explicit:
        touched_tokens = {
            index
            for indices in explicit
            for index in indices
            if 0 <= index < len(token_to_component)
        }
    else:
        touched_tokens = _lhs_token_indices(lhs_items, tokens)

    return sorted(
        {
            int(token_to_component[index])
            for index in touched_tokens
            if 0 <= index < len(token_to_component) and token_to_component[index] is not None
        }
    )


def project_raise_rule_to_components(
    sentence: str,
    tokenized_text: list[str] | None,
    rule: dict,
) -> list[str]:
    display, _ = _display_components(sentence)
    return [
        display[index]
        for index in project_raise_rule_to_component_indices(sentence, tokenized_text, rule)
        if 0 <= index < len(display)
    ]


def aggregate_component_raise_values(
    sentence: str,
    tokenized_text: list[str] | None,
    rules: Iterable[dict],
    *,
    weight_key: str = "score",
    drop_zero: bool = True,
) -> dict[str, float]:
    """Distribute each rule's weight evenly over the components it touches."""
    display, _ = _display_components(sentence)
    scores = [0.0] * len(display)
    for rule in rules:
        touched = project_raise_rule_to_component_indices(sentence, tokenized_text, rule)
        if not touched:
            continue
        weight = rule.get(weight_key)
        if weight is None:
            weight = rule.get("score", rule.get("wracc", rule.get("improvement", 0.0)))
        share = float(weight or 0.0) / len(touched)
        for index in touched:
            scores[index] += share
    return {
        component: scores[index]
        for index, component in enumerate(display)
        if not drop_zero or scores[index] != 0.0
    }


def canonicalize_component_rules(
    sentence: str,
    tokenized_text: list[str] | None,
    hits_by_class: dict[str, list[dict]],
    *,
    weight_key: str = "score",
    top_k: int | None = 10,
) -> list[dict]:
    """Return de-duplicated human-readable per-event rule units."""
    dedup: dict[tuple[str, str], dict] = {}
    order = 0
    for class_name, rules in (hits_by_class or {}).items():
        for rule in rules or []:
            components = project_raise_rule_to_components(sentence, tokenized_text, rule)
            if not components:
                continue
            body = " & ".join(components)
            key = (str(class_name).upper(), body.lower())
            score = float(rule.get(weight_key, rule.get("score", rule.get("wracc", 0.0))) or 0.0)
            row = {
                "unit": f"{class_name}: {body}",
                "score": score,
                "polarity": 1 if score >= 0 else -1,
                "idxs": project_raise_rule_to_component_indices(sentence, tokenized_text, rule),
                "components": components,
                "category": str(class_name),
                "_order": order,
            }
            order += 1
            previous = dedup.get(key)
            if previous is None or abs(score) > abs(float(previous["score"])):
                if previous is not None:
                    row["_order"] = previous["_order"]
                dedup[key] = row
    rows = sorted(
        dedup.values(),
        key=lambda row: (-abs(float(row["score"])), int(row["_order"])),
    )
    if top_k is not None:
        rows = rows[: int(top_k)]
    for row in rows:
        row.pop("_order", None)
    return rows
