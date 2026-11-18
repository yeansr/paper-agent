"""
PDF 解析与分块
==============

用于精读用户上传的论文 PDF。用 pdfplumber / pypdf 提取文本，并把长论文切成
带重叠的小块（chunk），以便分批送入模型、避免超出上下文长度。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PdfDocument:
    """解析后的 PDF 文档。"""

    path: str
    text: str
    num_pages: int

    @property
    def is_empty(self) -> bool:
        # 文本层几乎为空，通常意味着是扫描件（需要 OCR）
        return len(self.text.strip()) < 50


def _extract_with_pdfplumber(path: str) -> tuple[str, int]:
    import pdfplumber

    texts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts), len(pdf.pages)


def _extract_with_pypdf(path: str) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    texts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(texts), len(reader.pages)


def read_pdf(path: str) -> PdfDocument:
    """读取 PDF 文本；优先 pdfplumber，失败则回退 pypdf。"""
    if not Path(path).exists():
        raise FileNotFoundError(f"找不到 PDF：{path}")
    try:
        text, pages = _extract_with_pdfplumber(path)
    except Exception:
        text, pages = _extract_with_pypdf(path)

    doc = PdfDocument(path=path, text=text.strip(), num_pages=pages)
    if doc.is_empty:
        # 给出明确的可操作提示，而不是返回空文本让后续静默失败
        raise ValueError(
            "该 PDF 几乎没有文本层，可能是扫描件，需要先做 OCR（如使用 tesseract）。"
        )
    return doc


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 400) -> list[str]:
    """按字符长度切分文本，相邻块保留少量重叠，避免在句中硬切断语义。

    实际会优先在段落/换行边界处切分，使每块尽量完整。
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # 在窗口内寻找最后一个换行作为更自然的切点
            boundary = text.rfind("\n", start + max_chars // 2, end)
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        # 下一块回退 overlap 字符，保证上下文衔接
        start = end - overlap if end < len(text) else end
    return [c for c in chunks if c]
