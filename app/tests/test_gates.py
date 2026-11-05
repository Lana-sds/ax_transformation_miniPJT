import pytest

from quiz import gates

SNAPSHOT = "# Title\n\nThe  StateGraph   class is the main\ngraph class to use. It is parameterized by a user defined `State` object.\n"


def test_normalize_nfkc_and_whitespace_only():
    assert gates.normalize("Ａ  b\n\tc") == "A b c"
    assert gates.normalize("**Bold** `code`") == "**Bold** `code`"  # 마크다운 기호는 그대로


def test_quote_match_passes_across_whitespace_differences():
    quote = "The StateGraph class is the main graph class to use."
    assert gates.check_quote(quote, SNAPSHOT) is None


def test_quote_match_is_case_sensitive():
    quote = "the stategraph class is the main graph class to use."
    assert gates.check_quote(quote, SNAPSHOT) == "quote_mismatch"


def test_quote_must_be_at_least_30_chars_after_normalize():
    assert gates.check_quote("StateGraph   class", SNAPSHOT) == "quote_too_short"


def test_page_must_be_in_allowlist():
    allowed = {"/oss/python/langgraph/graph-api"}
    assert gates.check_page("/oss/python/langgraph/graph-api", allowed) is None
    assert gates.check_page("/oss/python/other", allowed) == "page_not_allowed"


def test_segments_must_exist():
    assert gates.check_segments([{"segment_id": "s1", "en": "a", "ko": "가"}]) is None
    assert gates.check_segments([]) == "mapping_missing"
    assert gates.check_segments([{"segment_id": "s1", "en": "a", "ko": ""}]) == "mapping_missing"


def test_run_gates_collects_failures():
    question = {
        "segments": [],
        "grounding_records": [
            {"page": "/oss/python/other", "quote": "The StateGraph class is the main graph class to use."}
        ],
    }
    fails = gates.run_gates(question, snapshots={}, allowed_pages={"/oss/python/langgraph/graph-api"})
    assert fails == ["mapping_missing", "page_not_allowed"]


# --- T1.1: 단답 허용 답안 개수(4.4) ---

@pytest.mark.parametrize("n, expected", [
    (0, "accepted_answers_count"), (1, None), (5, None), (6, "accepted_answers_count"),
])
def test_short_answer_accepted_answers_must_be_1_to_5(n, expected):
    answers = [f"name_{i}" for i in range(n)]
    assert gates.check_accepted_answers(answers) == expected


def test_short_answer_accepted_answers_missing_counts_as_zero():
    assert gates.check_accepted_answers(None) == "accepted_answers_count"


def test_run_gates_checks_accepted_answers_only_for_short_format():
    base = {
        "segments": [{"segment_id": "s1", "en": "a", "ko": "가"}],
        "grounding_records": [
            {"page": "/oss/python/langgraph/graph-api", "quote": "The StateGraph class is the main graph class to use."}
        ],
    }
    snaps = {"/oss/python/langgraph/graph-api": SNAPSHOT}
    allowed = {"/oss/python/langgraph/graph-api"}
    assert gates.run_gates({**base, "format": "single"}, snaps, allowed) == []
    assert gates.run_gates({**base, "format": "short", "accepted_answers": []}, snaps, allowed) == [
        "accepted_answers_count"
    ]
    assert gates.run_gates({**base, "format": "short", "accepted_answers": ["StateGraph"]}, snaps, allowed) == []
    # 형식은 슬롯에 있으므로 인자로도 넘길 수 있다
    assert gates.run_gates({**base, "accepted_answers": ["a"] * 6}, snaps, allowed, fmt="short") == [
        "accepted_answers_count"
    ]


# --- T1.1: 단답 채점 정규화(4.4) ---

@pytest.mark.parametrize("raw, expected", [
    ("StateGraph", "stategraph"),
    ("  StateGraph  ", "stategraph"),
    ("State Graph", "stategraph"),
    ("State\tGraph\n", "stategraph"),
    ("`StateGraph`", "stategraph"),
    ("``add_node``", "add_node"),
    ("add_node()", "add_node"),
    ("`add_node()`", "add_node"),
    ("add_node ( )", "add_node"),
    ("StateGraph.add_node()", "stategraph.add_node"),
    ("ＳｔａｔｅＧｒａｐｈ", "stategraph"),
    ("f(x)", "f(x)"),
    ("a()b", "a()b"),
])
def test_normalize_short_answer(raw, expected):
    assert gates.normalize_short_answer(raw) == expected


# --- T1.1: 유사 중복(4.4) ---

def _q(qid, stem, quote="x" * 40):
    return {"question_id": qid, "stem_en": stem, "grounding_records": [{"page": "/p", "quote": quote}]}


def test_stem_tokens_ignore_case_and_punctuation():
    assert gates.stem_tokens("What does `StateGraph` do?") == {"what", "does", "stategraph", "do"}


def test_jaccard_060_is_duplicate():
    # 공통 3, 각자 1개 더 -> 3/5 = 0.60
    a = _q("q1", "alpha beta gamma delta", quote="a" * 40)
    b = _q("q2", "alpha beta gamma epsilon", quote="b" * 40)
    assert gates.jaccard(gates.stem_tokens(a["stem_en"]), gates.stem_tokens(b["stem_en"])) == pytest.approx(0.60)
    assert gates.find_duplicate(a, [b]) == "q2"


def test_jaccard_059_is_not_duplicate():
    # 공통 59, a만 20, b만 21 -> 59/100 = 0.59
    common = [f"c{i}" for i in range(59)]
    a = _q("q1", " ".join(common + [f"a{i}" for i in range(20)]), quote="a" * 40)
    b = _q("q2", " ".join(common + [f"b{i}" for i in range(21)]), quote="b" * 40)
    assert gates.jaccard(gates.stem_tokens(a["stem_en"]), gates.stem_tokens(b["stem_en"])) == pytest.approx(0.59)
    assert gates.find_duplicate(a, [b]) is None


def test_jaccard_060_with_large_sets_is_duplicate():
    # 공통 60, a만 20, b만 20 -> 60/100 = 0.60
    common = [f"c{i}" for i in range(60)]
    a = _q("q1", " ".join(common + [f"a{i}" for i in range(20)]), quote="a" * 40)
    b = _q("q2", " ".join(common + [f"b{i}" for i in range(20)]), quote="b" * 40)
    assert gates.find_duplicate(a, [b]) == "q2"


def test_same_quote_is_duplicate_even_if_stems_differ():
    a = _q("q1", "completely different words here", quote="The StateGraph class is the main graph class to use.")
    b = _q("q2", "nothing shared at all", quote="The  StateGraph class is the main\ngraph class to use.")
    assert gates.find_duplicate(a, [b]) == "q2"


def test_find_duplicate_skips_self_and_returns_none_when_clear():
    a = _q("q1", "alpha beta gamma delta", quote="a" * 40)
    assert gates.find_duplicate(a, [a]) is None
    assert gates.find_duplicate(a, []) is None
    assert gates.find_duplicate(a, [_q("q2", "one two three four", quote="b" * 40)]) is None


def test_check_duplicate_returns_reason_and_target():
    a = _q("q1", "alpha beta gamma delta", quote="a" * 40)
    b = _q("q2", "alpha beta gamma delta", quote="b" * 40)
    assert gates.check_duplicate(a, [b]) == ("duplicate", "q2")
    assert gates.check_duplicate(a, []) == (None, None)
