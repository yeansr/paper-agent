"""
报告生成
========

把 ResearchOutput 组装为带引用链接的 Markdown 报告并落盘，保证每个结论都能
追溯到具体论文（课程强调的"引用可追溯"）。
"""

from __future__ import annotations

import time
from pathlib import Path

from .research_agent import ResearchOutput


def build_report(output: ResearchOutput) -> str:
    """组装完整 Markdown 报告。"""
    lines: list[str] = []
    lines.append(f"# 论文研究报告：{output.topic}")
    lines.append(f"\n> 生成时间：{time.strftime('%Y-%m-%d %H:%M')}　|　数据源：arXiv / 用户 PDF\n")

    # 论文清单（联网模式）
    if output.papers:
        lines.append("## 入选论文清单\n")
        for i, p in enumerate(output.papers, 1):
            lines.append(
                f"{i}. **{p.title}**（{p.arxiv_id}）\n"
                f"   - 摘要页：{p.abs_url}\n"
                f"   - PDF：{p.pdf_url}\n"
                f"   - 发布：{p.published[:10]}　分类：{', '.join(p.categories[:4])}\n"
            )

    # 精读笔记
    lines.append("## 精读笔记\n")
    for name, note in output.digests:
        lines.append(f"### {name}\n")
        lines.append(note.strip() + "\n")

    # 创新点 / idea
    lines.append("## 创新点与 Idea\n")
    lines.append(output.ideas.strip() + "\n")

    return "\n".join(lines)


def save_report(output: ResearchOutput, out_dir: str) -> str:
    """把报告写入指定目录，返回文件路径。"""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in output.topic if c.isalnum() or c in "_-")[:20] or "research"
    path = Path(out_dir) / f"报告_{safe_topic}_{stamp}.md"
    path.write_text(build_report(output), encoding="utf-8")
    return str(path)
