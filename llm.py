"""
大模型客户端
============

提供两种实现，统一接口 ``chat(messages) -> str``：

- ``LLMClient``  : 真实客户端，用 OpenAI SDK 对接 DeepSeek / 豆包等兼容端点；
- ``MockLLM``    : 离线客户端，按预置脚本响应，无需 Key 即可验证全流程。

业务代码只依赖 ``BaseChatClient`` 抽象，切换真实 / 离线模式时其余代码不变。
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Protocol

from .config import LLMConfig


class BaseChatClient(Protocol):
    """统一的对话客户端协议。"""

    name: str

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        ...


class LLMClient:
    """OpenAI 兼容的真实大模型客户端（DeepSeek / 豆包等）。"""

    def __init__(self, config: LLMConfig) -> None:
        if not config.api_key:
            raise RuntimeError(
                "未检测到 LLM_API_KEY，请先在 .env 中配置（参考 .env.example）。"
            )
        # 延迟导入 openai：离线 Mock 模式无需安装
        from openai import OpenAI

        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.model = config.model
        self.name = f"{config.provider}:{config.model}"

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        """调用 chat/completions，返回文本内容。"""
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""


class MockLLM:
    """离线脚本客户端：按顺序返回预置响应，用于无 Key 时的流程验证。

    脚本元素支持：
    - 字符串：直接作为本次响应；
    - 可调用对象 ``fn(messages) -> str``：根据当前输入动态生成。
    """

    def __init__(self, script: list[Any], name: str = "mock-llm") -> None:
        self._script = list(script)
        self._cursor = 0
        self.name = name

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        if self._cursor >= len(self._script):
            return "[Mock 脚本已结束]"
        item = self._script[self._cursor]
        self._cursor += 1
        return item(messages) if callable(item) else item


def get_client(force_mock: bool = False, mock_script: Optional[list[Any]] = None) -> BaseChatClient:
    """工厂方法：默认构建真实客户端；``force_mock=True`` 时构建离线客户端。"""
    if force_mock:
        return MockLLM(mock_script or [])
    from .config import load_config

    return LLMClient(load_config())
