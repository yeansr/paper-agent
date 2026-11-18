"""
paper_agent —— 论文研究 Agent
=============================

专为看论文、追前沿、提炼创新点和 idea 设计。

- config        : 配置加载（DeepSeek / 豆包等国产模型）
- llm           : 真实客户端 + 离线 Mock
- arxiv_client  : arXiv 免费检索
- pdf_reader    : PDF 解析与分块
- prompts       : 各环节提示词
- research_agent: 研究主流程（联网 / PDF 两条工作流）
- report        : 带引用的 Markdown 报告
"""

from .config import LLMConfig, load_config
from .llm import LLMClient, MockLLM, get_client
from .arxiv_client import ArxivClient, Paper, CS_CATEGORIES
from .pdf_reader import read_pdf, chunk_text, PdfDocument
from .research_agent import ResearchAgent, ResearchOutput
from .report import build_report, save_report

__all__ = [
    "LLMConfig",
    "load_config",
    "LLMClient",
    "MockLLM",
    "get_client",
    "ArxivClient",
    "Paper",
    "CS_CATEGORIES",
    "read_pdf",
    "chunk_text",
    "PdfDocument",
    "ResearchAgent",
    "ResearchOutput",
    "report",
    "build_report",
    "save_report",
]
