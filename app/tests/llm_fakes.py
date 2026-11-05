"""테스트용 가짜 구조화 출력 모델. Bedrock을 부르지 않는다."""

from langchain_core.messages import AIMessage

USAGE = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}


class FakeStructured:
    def __init__(self, parent, schema):
        self.parent, self.schema = parent, schema

    def invoke(self, prompt):
        self.parent.prompts.append(prompt)
        self.parent.schemas.append(self.schema)
        payload = self.parent.next_payload()
        raw = AIMessage(content="", usage_metadata=dict(USAGE))
        if payload is None:
            return {"raw": raw, "parsed": None, "parsing_error": ValueError("bad")}
        return {"raw": raw, "parsed": self.schema.model_validate(payload), "parsing_error": None}


class FakeModel:
    """payload가 리스트면 호출마다 차례로 쓰고, 끝나면 마지막 값을 되풀이한다. 아니면 늘 같은 값을 쓴다."""

    def __init__(self, payload):
        self.payload = payload
        self.prompts: list[str] = []
        self.schemas: list[type] = []

    def next_payload(self):
        if isinstance(self.payload, list):
            idx = min(len(self.prompts) - 1, len(self.payload) - 1)
            return self.payload[idx]
        return self.payload

    def with_structured_output(self, schema, include_raw=False):
        assert include_raw
        return FakeStructured(self, schema)
