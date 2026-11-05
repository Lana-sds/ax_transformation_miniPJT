import pytest

from quiz import gates, grading


def test_single_exact_key():
    q = {"answer_key": ["B"]}
    assert grading.grade("single", grading.normalize_answer("B"), q) is True
    assert grading.grade("single", grading.normalize_answer("A"), q) is False


def test_code_exact_key():
    q = {"answer_key": ["C"]}
    assert grading.grade("code", grading.normalize_answer("C"), q) is True
    assert grading.grade("code", grading.normalize_answer("D"), q) is False


def test_multi_exact_set_any_order():
    q = {"answer_key": ["C", "A"]}
    assert grading.grade("multi", grading.normalize_answer(["A", "C"]), q) is True
    assert grading.grade("multi", grading.normalize_answer(["C", "A"]), q) is True


def test_multi_has_no_partial_credit():
    q = {"answer_key": ["A", "C"]}
    assert grading.grade("multi", grading.normalize_answer(["A"]), q) is False
    assert grading.grade("multi", grading.normalize_answer(["A", "B", "C"]), q) is False
    assert grading.grade("multi", grading.normalize_answer(["B", "D"]), q) is False
    assert grading.grade("multi", grading.normalize_answer([]), q) is False


def test_short_matches_accepted_answers_after_normalization():
    q = {"answer_key": [], "accepted_answers": ["StateGraph", "langgraph.graph.StateGraph"]}
    for ans in ["StateGraph", "stategraph", " `StateGraph` ", "StateGraph()", "State Graph", "LangGraph.Graph.StateGraph"]:
        assert grading.grade("short", grading.normalize_answer(ans), q) is True, ans


def test_short_wrong_answers():
    q = {"accepted_answers": ["add_node"]}
    for ans in ["add_edge", "", "   ", "add_node_x", "addnode"]:
        assert grading.grade("short", grading.normalize_answer(ans), q) is False, ans


def test_short_normalizes_accepted_answers_too():
    q = {"accepted_answers": ["`add_node()`"]}
    assert grading.grade("short", grading.normalize_answer("add_node"), q) is True


def test_short_rejects_multiple_submitted_values():
    q = {"accepted_answers": ["add_node"]}
    assert grading.grade("short", ["add_node", "x"], q) is False


def test_short_uses_gates_normalization():
    assert grading.normalize_short_answer is gates.normalize_short_answer


def test_short_without_accepted_answers_is_wrong():
    assert grading.grade("short", ["x"], {"answer_key": ["x"]}) is False


def test_unknown_format_raises_clear_error():
    with pytest.raises(grading.UnknownFormatError, match="essay"):
        grading.grade("essay", ["A"], {"answer_key": ["A"]})


def test_unknown_format_error_is_value_error():
    assert issubclass(grading.UnknownFormatError, ValueError)


def test_all_four_formats_registered():
    assert {"single", "multi", "short", "code"} <= set(grading.registered_formats())


def test_register_new_format_without_db_change():
    @grading.register("always_true_test")
    def _g(answer, question):
        return True

    try:
        assert grading.grade("always_true_test", ["x"], {}) is True
    finally:
        grading.unregister("always_true_test")
    with pytest.raises(grading.UnknownFormatError):
        grading.grade("always_true_test", ["x"], {})
