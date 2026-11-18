"""
arXiv 检索客户端
================

arXiv 提供免费、稳定、无需 Key 的 API，覆盖计算机科学（cs.*）全部预印本，
是 CS/AI 方向追踪前沿的首选源。本模块用标准库解析其 Atom XML，不依赖
feedparser。

支持：
- 按关键词检索（可限定只搜标题）；
- 按 arXiv 分类过滤（cs.AI / cs.LG / cs.CL / cs.CV 等）；
- 按提交日期倒序，拿最新论文；
- 提取标题、摘要、作者、日期、分类、PDF 与摘要页链接。
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

import requests

API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# 常用 CS 分类，便于调用方按方向检索
CS_CATEGORIES = {
    "AI": "cs.AI",      # 人工智能
    "LG": "cs.LG",      # 机器学习
    "CL": "cs.CL",      # 自然语言处理 / 计算语言学
    "CV": "cs.CV",      # 计算机视觉
    "RO": "cs.RO",      # 机器人
    "CL_": "cs.CL",
}


@dataclass
class Paper:
    """一篇论文的结构化信息。"""

    arxiv_id: str
    title: str
    summary: str
    authors: list[str]
    published: str
    updated: str
    categories: list[str]
    abs_url: str
    pdf_url: str
    comment: str = ""

    def brief(self) -> str:
        """生成给模型看的精简文本（标题 + 摘要 + 链接）。"""
        return (
            f"ID: {self.arxiv_id}\n标题: {self.title}\n"
            f"摘要: {self.summary}\n链接: {self.abs_url}\n"
            f"分类: {', '.join(self.categories)}"
        )


def _build_query(keywords: list[str], category: Optional[str], title_only: bool) -> str:
    """构造 arXiv 查询表达式。"""
    field = "ti" if title_only else "all"
    parts: list[str] = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        # 含空格的短语用引号包裹，保证整体匹配
        parts.append(f'{field}:"{kw}"' if " " in kw else f"{field}:{kw}")
    query = " AND ".join(parts)
    if category:
        cat = CS_CATEGORIES.get(category.upper(), category)
        query = f"({query}) AND cat:{cat}" if query else f"cat:{cat}"
    return query


class ArxivClient:
    """arXiv API 封装。"""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def search(
        self,
        keywords: list[str],
        category: Optional[str] = None,
        max_results: int = 10,
        title_only: bool = False,
    ) -> list[Paper]:
        """检索论文，按提交日期倒序返回。"""
        params = {
            "search_query": _build_query(keywords, category, title_only),
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        resp = requests.get(API_URL, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return self._parse_feed(resp.text)

    def _parse_feed(self, xml_text: str) -> list[Paper]:
        root = ET.fromstring(xml_text)
        papers: list[Paper] = []

        for entry in root.findall("a:entry", ATOM_NS):
            raw_id = entry.findtext("a:id", default="", namespaces=ATOM_NS).strip()
            # 从 URL 中提取 arXiv ID，如 .../abs/2401.00001v1 -> 2401.00001
            arxiv_id = raw_id.rsplit("/", 1)[-1]
            base_id = re.sub(r"v\d+$", "", arxiv_id)

            title = " ".join(
                entry.findtext("a:title", default="", namespaces=ATOM_NS).split()
            )
            summary = " ".join(
                entry.findtext("a:summary", default="", namespaces=ATOM_NS).split()
            )
            authors = [
                a.findtext("a:name", default="", namespaces=ATOM_NS)
                for a in entry.findall("a:author", ATOM_NS)
            ]
            categories = [c.get("term", "") for c in entry.findall("a:category", ATOM_NS)]

            # 定位 PDF 链接；找不到则按 ID 规则拼一个
            pdf_url = f"https://arxiv.org/pdf/{base_id}.pdf"
            for link in entry.findall("a:link", ATOM_NS):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", pdf_url)

            comment = entry.findtext("arxiv:comment", default="", namespaces=ATOM_NS) or ""

            papers.append(
                Paper(
                    arxiv_id=base_id,
                    title=title,
                    summary=summary,
                    authors=authors,
                    published=entry.findtext("a:published", default="", namespaces=ATOM_NS),
                    updated=entry.findtext("a:updated", default="", namespaces=ATOM_NS),
                    categories=categories,
                    abs_url=f"https://arxiv.org/abs/{base_id}",
                    pdf_url=pdf_url,
                    comment=comment,
                )
            )
        return papers
