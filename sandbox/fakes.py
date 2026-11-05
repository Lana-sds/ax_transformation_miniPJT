"""코드형 문제 exec_spec이 import하는 가짜 모델(GR-7.3). 오프라인 전용이고 Bedrock을 부르지 않는다.

사용 예:
    from langchain_core.messages import AIMessage
    from fakes import GenericFakeChatModel, ToolCallingFakeChatModel

    model = GenericFakeChatModel(messages=iter(["Hello"]))
    model.invoke("hi").content  # "Hello"

    model = ToolCallingFakeChatModel(messages=iter([
        AIMessage(content="", tool_calls=[{"name": "add", "args": {"a": 1, "b": 2}, "id": "call_1"}]),
        AIMessage(content="3"),
    ]))
    agent = create_agent(model, tools=[add])  # bind_tools가 같은 대본을 이어 쓴다
"""

from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

__all__ = ["GenericFakeChatModel", "ToolCallingFakeChatModel"]


class ToolCallingFakeChatModel(GenericFakeChatModel):
    """`bind_tools`를 지원하는 GenericFakeChatModel.

    `bind_tools`는 도구 목록을 무시하고 자기 자신을 돌려준다. 그래서 묶은 모델도 같은
    `messages` 반복자를 이어 쓴다. 도구 호출은 대본의 `AIMessage.tool_calls`로 낸다.
    """

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self
