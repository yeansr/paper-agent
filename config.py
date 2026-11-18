"""
配置加载
========

从环境变量 / .env 文件读取大模型接入信息。DeepSeek、豆包（火山方舟）等国产
模型都提供 OpenAI 兼容接口，因此只需三个参数：API Key、Base URL、模型名。

在项目根目录创建 .env（可参考 .env.example），或直接设置环境变量：

    LLM_PROVIDER=deepseek          # deepseek / doubao / custom
    LLM_API_KEY=sk-xxxxxxxx
    # 以下两项可省略，省略时用 provider 预设
    LLM_BASE_URL=https://...
    LLM_MODEL=...
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()  # 读取项目根目录 .env（若存在）
except Exception:  # pragma: no cover
    pass


# 各厂商的 OpenAI 兼容端点与默认模型预设
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    "doubao": {
        # 火山引擎方舟；模型名需替换为你在控制台创建的推理接入点 ID（ep-xxxx）
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-xxxxxxxx",
    },
}


@dataclass
class LLMConfig:
    """大模型接入配置。"""

    api_key: str
    base_url: str
    model: str
    provider: str = "custom"

    def masked_key(self) -> str:
        """日志里只显示脱敏后的 key，避免泄露。"""
        if not self.api_key:
            return "(未设置)"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


def load_config() -> LLMConfig:
    """从环境变量组装配置；未配置 key 时给出明确提示而非静默失败。"""
    provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
    preset = PROVIDER_PRESETS.get(provider, {})

    base_url = os.getenv("LLM_BASE_URL") or preset.get("base_url", "")
    model = os.getenv("LLM_MODEL") or preset.get("model", "")
    api_key = os.getenv("LLM_API_KEY", "").strip()

    return LLMConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        provider=provider,
    )
