"""
研究 Agent 主流程
=================

把各模块编排为两条完整工作流，对应课程"深度研究 Agent"模式：

- 联网模式 ``search_and_ideate``：
  检索 arXiv → LLM 相关性筛选 → 逐篇精读归纳 → 横向对比提炼 idea；
- PDF 模式 ``analyze_pdfs``：
  解析 PDF → 分块（map-reduce 精读，支持超长论文）→ 汇总提炼 idea。

模型只负责理解与生成，检索、解析、流程控制都由本模块在 Python 侧完成，
并在每一步打印进度，方便观察。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .llm import BaseChatClient
from .arxiv_client import ArxivClient, Paper
from .pdf_reader import read_pdf, chunk_text
from . import prompts


# 进度回调：接收一句人类可读的进度文字（网页端用它刷新状态条）
ProgressFn = Callable[[str], None]


# ---------------------------------------------------------------------------
# 解析"相关性筛选"输出
# ---------------------------------------------------------------------------
def _parse_keep(text: str) -> list[str]:
    kept: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("KEEP:"):
            pid = line.split(":", 1)[1].strip()
            if pid and pid.upper() != "NONE":
                kept.append(pid)
    return kept


@dataclass
class ResearchOutput:
    """一次研究的完整产出。"""

    topic: str
    papers: list[Paper] = field(default_factory=list)
    digests: list[tuple[str, str]] = field(default_factory=list)  # (论文ID, 精读笔记)
    ideas: str = ""


class ResearchAgent:
    """论文研究 Agent。"""

    def __init__(
        self,
        llm: BaseChatClient,
        arxiv: Optional[ArxivClient] = None,
        progress: Optional[ProgressFn] = None,
    ) -> None:
        self.llm = llm
        self.arxiv = arxiv or ArxivClient()
        # 可选进度回调；网页端传入后即可实时显示当前阶段
        self.progress = progress

    def _emit(self, message: str) -> None:
        """同时输出到控制台与进度回调（若有）。"""
        print(message)
        if self.progress is not None:
            self.progress(message)

    def _chat(self, user_content: str, system: str = prompts.SYSTEM_RESEARCHER) -> str:
        return self.llm.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ]
        )

    # =====================================================================
    # 工作流一：联网检索 + idea 提炼
    # =====================================================================
    def search_and_ideate(
        self,
        topic: str,
        keywords: list[str],
        category: Optional[str] = None,
        max_results: int = 15,
        top_k: int = 5,
    ) -> ResearchOutput:
        # 1) 检索候选论文
        self._emit(f"[1/4] 检索 arXiv：关键词={keywords} 分类={category}")
        candidates = self.arxiv.search(
            keywords=keywords, category=category, max_results=max_results
        )
        self._emit(f"      拿到 {len(candidates)} 篇候选")
        if not candidates:
            return ResearchOutput(topic=topic, ideas="未检索到相关论文，建议更换关键词。")

        # 2) LLM 相关性筛选
        cand_text = "\n\n".join(p.brief() for p in candidates)
        screen = self._chat(prompts.SCREEN_PROMPT.format(topic=topic, candidates=cand_text))
        keep_ids = _parse_keep(screen)
        id_to_paper = {p.arxiv_id: p for p in candidates}
        selected = [id_to_paper[i] for i in keep_ids if i in id_to_paper]
        # 兜底：模型若没选出任何结果，则取前 top_k 篇，避免流程空转
        if not selected:
            selected = candidates[:top_k]
        selected = selected[:top_k]
        self._emit(f"[2/4] 筛选出 {len(selected)} 篇进入精读")

        # 3) 逐篇精读归纳
        digests: list[tuple[str, str]] = []
        for idx, paper in enumerate(selected, 1):
            self._emit(f"[3/4] 精读 {idx}/{len(selected)}：{paper.title[:40]}")
            note = self._chat(prompts.DIGEST_PROMPT.format(paper=paper.brief()))
            digests.append((paper.arxiv_id, note))

        # 4) 横向对比，提炼 idea
        self._emit("[4/4] 横向对比，提炼创新点")
        digest_text = "\n\n".join(
            f"论文 {pid} 笔记：\n{note}" for pid, note in digests
        )
        ideas = self._chat(prompts.IDEA_PROMPT.format(topic=topic, digests=digest_text))

        return ResearchOutput(
            topic=topic, papers=selected, digests=digests, ideas=ideas
        )

    # =====================================================================
    # 工作流二：PDF 精读 + idea 提炼（map-reduce 支持超长论文）
    # =====================================================================
    def analyze_pdfs(self, pdf_paths: list[str], title: Optional[str] = None) -> ResearchOutput:
        all_notes: list[tuple[str, str]] = []

        for path in pdf_paths:
            self._emit(f"[PDF] 解析：{path}")
            doc = read_pdf(path)
            chunks = chunk_text(doc.text)
            name = title or path.split("/")[-1]

            if len(chunks) == 1:
                # 单块：直接精读
                note = self._chat(
                    prompts.PDF_DIGEST_PROMPT.format(title=name, content=chunks[0])
                )
            else:
                # 多块：先逐块总结（map），再把块总结合并成整篇笔记（reduce）
                self._emit(f"      论文较长，分为 {len(chunks)} 块做 map-reduce 精读")
                partials = [
                    self._chat(
                        prompts.PDF_DIGEST_PROMPT.format(
                            title=f"{name}（第{i+1}部分）", content=chunk
                        )
                    )
                    for i, chunk in enumerate(chunks)
                ]
                note = self._chat(
                    prompts.PDF_DIGEST_PROMPT.format(
                        title=name, content="\n\n".join(partials)
                    )
                )
            all_notes.append((name, note))

        # 汇总所有 PDF 笔记，提炼 idea
        notes_text = "\n\n".join(f"《{n}》笔记：\n{nt}" for n, nt in all_notes)
        ideas = self._chat(prompts.PDF_IDEA_PROMPT.format(notes=notes_text))

        return ResearchOutput(topic=title or "PDF 精读", digests=all_notes, ideas=ideas)
