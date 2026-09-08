from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

_IPV4 = re.compile(
    r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])"
)
_IPV6 = re.compile(r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b", re.I)
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.I,
)
_HEX = re.compile(r"\b[0-9a-f]{8,}\b", re.I)
_NUM = re.compile(r"[-+]?(?:\d+\.\d+|\d+)")
_PATH = re.compile(r"(?:[A-Za-z]:\\|/)(?:[^\s:]+)")
_URL = re.compile(r"\bhttps?://\S+")
_EMAIL = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.I)
_WS_MULTI = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9_<>\-/\.]+")


def canonicalize(
    value: str,
    *,
    keep_numbers: bool = True,
    numbers_mode: str = "canonical",
) -> str:
    """Canonicalize common log fields while retaining the overall lexical structure."""
    text = str(value).strip().lower()
    text = _URL.sub("<url>", text)
    text = _EMAIL.sub("<email>", text)
    text = _IPV4.sub("<ip>", text)
    text = _IPV6.sub("<ip>", text)
    text = _UUID.sub("<uuid>", text)
    text = _PATH.sub("<path>", text)
    text = _HEX.sub("<hex>", text)

    if not keep_numbers:
        if numbers_mode == "binned":

            def _bin(match: re.Match[str]) -> str:
                try:
                    number = float(match.group(0))
                except ValueError:
                    return "<num>"
                if number < 0:
                    return "<num:neg>"
                if number < 10:
                    return "<num:0-9>"
                if number < 100:
                    return "<num:10-99>"
                if number < 1000:
                    return "<num:100-999>"
                return "<num:1k+>"

            text = _NUM.sub(_bin, text)
        else:
            text = _NUM.sub("<num>", text)
    return _WS_MULTI.sub(" ", text)


def basic_tokens(value: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(value) if token]


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    size = len(value)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def extract_shape_items(raw: str) -> set[str]:
    """Return coarse, intentionally low-dimensional log-shape indicators."""
    text = str(raw)
    size = len(text)
    if size == 0:
        return {
            "len=q1",
            "entropy=q1",
            "digit_ratio=q1",
            "upper_ratio=q1",
            "symbol_ratio=q1",
        }

    digits = sum(ch.isdigit() for ch in text)
    uppers = sum(ch.isupper() for ch in text)
    symbols = sum(not ch.isalnum() and not ch.isspace() for ch in text)
    has_kv = int(bool(re.search(r"\b\w+=\S+", text)))
    has_stack = int("exception" in text.lower() or bool(re.search(r"^\s*at\s+\S+", text, re.I)))

    def tertile(value: float, cuts: tuple[float, float] = (0.33, 0.66)) -> str:
        if value <= cuts[0]:
            return "q1"
        if value <= cuts[1]:
            return "q2"
        return "q3"

    return {
        f"len={tertile(size / 2000.0)}",
        f"entropy={tertile(shannon_entropy(text) / 8.0)}",
        f"digit_ratio={tertile(digits / size)}",
        f"upper_ratio={tertile(uppers / size)}",
        f"symbol_ratio={tertile(symbols / size)}",
        f"has_json={int('{' in text and '}' in text and ':' in text)}",
        f"has_kv={has_kv}",
        f"has_stack={has_stack}",
        f"has_ip={int('<ip>' in text)}",
        f"has_path={int('<path>' in text)}",
        f"has_url={int('<url>' in text)}",
    }


class VocabBuilder:
    """Document-frequency vocabulary used by the symbolic transaction builder."""

    def __init__(
        self,
        max_unigrams: int = 3000,
        min_df: float = 0.005,
        max_df: float = 0.60,
        max_bigrams: int = 500,
        min_df_bigram: float = 0.003,
        seed: int = 13,
    ) -> None:
        self.max_unigrams = int(max_unigrams)
        self.min_df = float(min_df)
        self.max_df = float(max_df)
        self.max_bigrams = int(max_bigrams)
        self.min_df_bigram = float(min_df_bigram)
        self.seed = int(seed)
        self.unigrams_: set[str] = set()
        self.bigrams_: set[tuple[str, str]] = set()

    def fit(self, canon_lines: Iterable[str]) -> VocabBuilder:
        lines = list(canon_lines)
        if not lines:
            raise ValueError("cannot fit a vocabulary on an empty corpus")
        return self.fit_tokens([basic_tokens(line) for line in lines])

    def fit_tokens(self, token_seqs: Iterable[Iterable[str]]) -> VocabBuilder:
        seqs = [list(seq) for seq in token_seqs]
        if not seqs:
            raise ValueError("cannot fit a vocabulary on an empty corpus")
        n = len(seqs)
        df_unigram: Counter[str] = Counter()
        for seq in seqs:
            df_unigram.update(set(seq))
        candidates = [
            token for token, df in df_unigram.items() if self.min_df <= (df / n) <= self.max_df
        ]
        candidates.sort(key=lambda token: (-df_unigram[token], token))
        self.unigrams_ = set(candidates[: self.max_unigrams])

        if self.max_bigrams <= 0:
            self.bigrams_ = set()
            return self

        df_bigram: Counter[tuple[str, str]] = Counter()
        for seq in seqs:
            df_bigram.update(set(zip(seq, seq[1:], strict=False)))
        scored: list[tuple[tuple[str, str], float]] = []
        for (left, right), count in df_bigram.items():
            if count / n < self.min_df_bigram:
                continue
            p_pair = count / n
            p_left = df_unigram.get(left, 0) / n
            p_right = df_unigram.get(right, 0) / n
            pmi = math.log((p_pair + 1e-12) / (p_left * p_right + 1e-12))
            scored.append(((left, right), pmi))
        scored.sort(key=lambda item: (-item[1], item[0]))
        self.bigrams_ = {pair for pair, _ in scored[: self.max_bigrams]}
        return self

    def items_from(self, canon_line: str) -> set[str]:
        return self.items_from_tokens(basic_tokens(canon_line))

    def items_from_tokens(self, tokens: Iterable[str]) -> set[str]:
        seq = list(tokens)
        items = {f"tok={token}" for token in seq if token in self.unigrams_}
        for left, right in zip(seq, seq[1:], strict=False):
            if (left, right) in self.bigrams_:
                items.add(f"ng={left}_{right}")
        return items
