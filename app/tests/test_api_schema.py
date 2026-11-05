"""`/openapi.json`이 API 명세 역할을 한다(design.md 7.1).

응답 모델은 정의에 없는 필드를 거절한다(`extra="forbid"`). 그래서 서버가 모델과 다른 필드를 돌려주면
`test_api.py`, `test_audit.py`의 API 테스트가 실패한다. 이 파일은 명세 자체가 비어 있지 않은지 본다.
"""

import pytest

from quiz.server import app

SPEC = app.openapi()
OPERATIONS = [
    (path, method, op)
    for path, item in SPEC["paths"].items()
    if path.startswith("/api/")
    for method, op in item.items()
]

# 409를 낼 수 있는 경로(design.md 8.6)
CONFLICT_ROUTES = {
    ("/api/sets", "post"),
    ("/api/sets/{set_id}/answers", "post"),
    ("/api/attempts/{attempt_id}/tag", "put"),
    ("/api/audits", "post"),
}

# 404를 낼 수 있는 경로
NOT_FOUND_ROUTES = {
    ("/api/sets/{set_id}", "get"),
    ("/api/sets/{set_id}/answers", "post"),
    ("/api/attempts/{attempt_id}/tag", "put"),
    ("/api/audits/current", "get"),
    ("/api/audits/{audit_id}/records/{question_id}", "put"),
}


def _schema(ref: dict) -> dict:
    return SPEC["components"]["schemas"][ref["$ref"].rsplit("/", 1)[-1]]


def test_all_eight_routes_are_in_spec():
    assert len(OPERATIONS) == 8


@pytest.mark.parametrize(("path", "method", "op"), OPERATIONS, ids=[f"{m} {p}" for p, m, _ in OPERATIONS])
def test_success_response_has_named_schema(path, method, op):
    schema = op["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" in schema, f"{method} {path} has no response model"
    assert _schema(schema)["properties"]


@pytest.mark.parametrize(("path", "method"), sorted(CONFLICT_ROUTES))
def test_conflict_response_documents_reason(path, method):
    schema = SPEC["paths"][path][method]["responses"]["409"]["content"]["application/json"]["schema"]
    detail = _schema(_schema(schema)["properties"]["detail"])
    assert set(detail["properties"]["reason"]["enum"]) == {
        "untagged_wrong", "set_closed", "correct_row", "already_answered", "pool_too_small", "no_pool",
    }


@pytest.mark.parametrize(("path", "method"), sorted(NOT_FOUND_ROUTES))
def test_not_found_response_is_documented(path, method):
    assert "404" in SPEC["paths"][path][method]["responses"]
