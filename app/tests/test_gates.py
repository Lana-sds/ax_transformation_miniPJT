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
