"""
示例二：上传 PDF 精读并提炼 idea
================================

真实模式（需 .env 配置 Key，并指定 PDF 路径）：
    python examples/run_pdf.py /path/to/paper.pdf

离线 Mock 模式（自动生成一个测试 PDF，无需 Key）：
    python examples/run_pdf.py --mock
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from paper_agent import ResearchAgent, get_client, MockLLM, save_report

ROOT = pathlib.Path(__file__).resolve().parent.parent


def create_sample_pdf() -> str:
    """用 reportlab 生成一个模拟论文 PDF（英文，避免默认字体不支持中文）。"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = ROOT / "papers" / "sample_paper.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    text = c.beginText(56, 740)
    text.setLeading(16)
    lines = [
        "Title: A Reflection-Based Tool Calling Framework for LLM Agents",
        "",
        "Abstract: We propose a framework that lets an LLM agent call external",
        "tools and repair its calls using runtime error feedback. Experiments on",
        "20 benchmark tasks show improved reliability over single-shot prompting.",
        "",
        "1. Introduction: LLM agents increasingly need to interact with external",
        "systems such as databases, search APIs and code executors. However, long",
        "chains of reasoning accumulate errors, and a single failed step breaks",
        "the whole workflow. We argue that objective runtime signals are the key.",
        "",
        "2. Method: Our agent first emits a tool intent (function name and JSON",
        "arguments). A Python executor validates arguments with a schema, runs the",
        "tool, and returns either the result or a readable error. On error, the",
        "agent revises only the failing step. A budget of max steps and tokens is",
        "enforced, and every step is logged as a trace for later analysis.",
        "",
        "3. Experiments: We evaluate on 20 tool-use tasks. The baseline single",
        "prompt achieves 77 percent success, while our reflection loop reaches",
        "90 percent. Most gains come from database and code execution errors.",
        "",
        "4. Conclusion: Runtime feedback and disciplined evals substantially",
        "improve agent reliability. Future work includes multi-agent permission",
        "governance and cross-domain tool transfer.",
    ]
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    return str(pdf_path)


def build_mock_llm() -> MockLLM:
    fake_note = (
        "### 论文概述\n提出基于反思的工具调用框架，用运行报错驱动修复。\n"
        "### 问题与动机\n长链条错误累积，单步失败会导致整体失败。\n"
        "### 方法详解\n模型出意图，执行器校验并执行，报错回填，局部重试。\n"
        "### 实验与结论\n20 个任务成功率从 77% 提升到 90%。\n"
        "### 创新点\n将客观运行信号引入工具调用循环。\n"
        "### 局限与可改进方向\n未涉及多 Agent 权限治理与跨域迁移。"
    )
    fake_idea = (
        "## 可延展的方向\n1. 多 Agent 工具权限治理；2. 跨域工具迁移；3. 调用可解释性。\n"
        "## 具体 Idea\n"
        "1. 统一鉴权中间件：在执行侧拦截所有工具调用，依据是论文的执行器设计，难点是多厂商兼容。\n"
        "2. 报错驱动的选择器：积累历史报错预测工具，难点是数据规模。\n"
        "3. 跨域工具迁移机制：把工具描述标准化，难点是语义对齐。\n"
        "## 与现有工作的差异化\n现有工作只做单 Agent，本方案扩展到权限治理与迁移。"
    )
    return MockLLM([fake_note, fake_idea], name="mock")


def main() -> None:
    mock = "--mock" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--mock"]

    if mock:
        pdf_path = create_sample_pdf()
        llm = build_mock_llm()
    else:
        if not args:
            print("真实模式请提供 PDF 路径，例如：python examples/run_pdf.py ./paper.pdf")
            print("或使用离线演示：python examples/run_pdf.py --mock")
            return
        pdf_path = args[0]
        llm = get_client()

    agent = ResearchAgent(llm=llm)
    output = agent.analyze_pdfs([pdf_path])

    report_path = save_report(
        output,
        out_dir=str(ROOT / "papers"),
    )
    print("\n报告已保存：", report_path)
    print("\n" + "=" * 60 + "\n创新点部分预览：\n")
    print(output.ideas)


if __name__ == "__main__":
    main()
