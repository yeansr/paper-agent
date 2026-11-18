"""
示例一：联网检索论文并提炼 idea
==============================

真实模式（需在 .env 配置 LLM_API_KEY）：
    python examples/run_search.py

离线 Mock 模式（无需 Key，arXiv 检索为真实调用，LLM 用脚本模拟）：
    python examples/run_search.py --mock
"""

import sys
import pathlib
import re

# 导入上一级的 paper_agent 包
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from paper_agent import ResearchAgent, get_client, MockLLM, save_report


# 研究主题与检索参数（可按你的方向修改）
TOPIC = "AI Agent 的自主规划与工具调用"
KEYWORDS = ["AI agent", "tool use"]
CATEGORY = "AI"          # 对应 cs.AI；也可填 LG/CL/CV，填 None 则不限分类


def build_mock_llm() -> MockLLM:
    """构造离线 Mock：动态适配真实检索到的论文 ID。"""

    def fake_screen(messages):
        # 从候选文本里提取第一个真实论文 ID，只保留它进入精读
        content = messages[-1]["content"]
        m = re.search(r"ID:\s*(\S+)", content)
        pid = m.group(1) if m else "unknown"
        return f"KEEP: {pid}"

    fake_digest = (
        "### 研究问题\n如何让 Agent 更可靠地选择并调用工具。\n"
        "### 核心方法\n用结构化工具描述 + 反思循环。\n"
        "### 主要创新\n提出可校验的工具调用框架。\n"
        "### 局限与不足\n长链条下错误仍会累积。\n"
        "### 可借鉴点\n报错回填驱动自我修复。"
    )
    fake_ideas = (
        "## 一、研究现状与共性\n现有工作聚焦单 Agent 工具调用，多步可靠性不足。\n"
        "## 二、研究空白\n1. 多 Agent 工具权限治理；2. 跨域工具迁移；3. 调用可解释性。\n"
        "## 三、候选创新点 / Idea\n"
        "1. 带权限策略的工具调用中间件：在执行侧统一鉴权，难点是兼容多厂商。\n"
        "2. 基于反思的工具选择纠错：用历史报错训练选择器，难点是数据积累。\n"
        "## 四、推荐的下一步\n先在 20 个任务上做工具选择准确率基线。"
    )
    return MockLLM([fake_screen, fake_digest, fake_ideas], name="mock")


def main(mock: bool) -> None:
    llm = build_mock_llm() if mock else get_client()
    agent = ResearchAgent(llm=llm)

    output = agent.search_and_ideate(
        topic=TOPIC,
        keywords=KEYWORDS,
        category=CATEGORY,
        max_results=10,
        top_k=3,
    )

    report_path = save_report(
        output,
        out_dir=str(pathlib.Path(__file__).resolve().parent.parent / "papers"),
    )
    print("\n报告已保存：", report_path)
    print("\n" + "=" * 60 + "\n创新点部分预览：\n")
    print(output.ideas)


if __name__ == "__main__":
    main(mock="--mock" in sys.argv)
