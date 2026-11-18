"""
论文研究 Agent —— 网页界面
==========================

用 Streamlit 把命令行版 Agent 做成可视化网页，在 Edge / Chrome 直接打开使用。

启动：
    streamlit run app.py
启动后终端会显示一个 http://localhost:8501 地址，Edge 打开即可。

界面包含两个功能页：
- 追前沿：联网检索 arXiv 并提炼创新点
- 精读 PDF：上传论文 PDF 做结构化精读

API Key 只在当前会话内存中使用，不写入磁盘、不保存到文件。
"""

from __future__ import annotations

import pathlib
import re
import sys
import tempfile
from typing import Any

import streamlit as st

# 让应用能导入同目录下的 paper_agent 包
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from paper_agent import (
    CS_CATEGORIES,
    MockLLM,
    ResearchAgent,
    build_report,
    get_client,
    save_report,
)

# ---------------------------------------------------------------------------
# 页面基础配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="论文研究 Agent",
    page_icon="static/icon-192.png",
    layout="wide",
)


def inject_pwa() -> None:
    """注入 PWA 清单与主题色，使安卓 Chrome 能识别并提示"安装/添加到主屏幕"。

    使用 st.html（非 iframe）直接插入页面；通过 JS 把清单与主题色显式挂到
    <head>，即使静态标签被 HTML 清理，JS 仍能动态补上。
    """
    st.html(
        """
        <link rel="manifest" href="static/manifest.json">
        <meta name="theme-color" content="#2f6fed">
        <script>
        (function () {
            if (!document.querySelector('link[rel="manifest"]')) {
                var link = document.createElement('link');
                link.rel = 'manifest';
                link.href = 'static/manifest.json';
                document.head.appendChild(link);
            }
            if (!document.querySelector('meta[name="theme-color"]')) {
                var meta = document.createElement('meta');
                meta.name = 'theme-color';
                meta.content = '#2f6fed';
                document.head.appendChild(meta);
            }
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


inject_pwa()

CUSTOM_CSS = """
<style>
    .main-title {font-size: 30px; font-weight: 700; margin-bottom: 4px;}
    .sub-title {color: #666; font-size: 14px; margin-bottom: 18px;}
    .hint {background: #f6f8fa; border-left: 3px solid #4b8bf5;
           padding: 10px 14px; border-radius: 4px; font-size: 13px; color: #444;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 离线演示用的 Mock 模型
# ---------------------------------------------------------------------------
def make_demo_llm() -> MockLLM:
    """构造一个能应对任意输入的演示模型，用于没有 API Key 时体验完整流程。"""

    def fake_screen(messages: list[dict[str, str]]) -> str:
        content = messages[-1]["content"]
        ids = re.findall(r"ID:\s*(\S+)", content)
        return "\n".join(f"KEEP: {i}" for i in ids[:2]) or "NONE"

    fake_digest = (
        "### 研究问题\n针对该主题的核心难点展开研究。\n"
        "### 核心方法\n采用结构化建模与迭代优化的方式。\n"
        "### 主要创新\n提出可验证的新机制。\n"
        "### 局限与不足\n在规模化场景下仍有提升空间。\n"
        "### 可借鉴点\n客观反馈驱动的迭代改进思路。"
    )
    fake_ideas = (
        "## 一、研究现状与共性\n现有工作在单任务上表现良好，跨场景泛化不足。\n"
        "## 二、研究空白\n"
        "1. 跨域迁移机制缺失；2. 缺乏统一评估基准；3. 可解释性不足。\n"
        "## 三、候选创新点 / Idea\n"
        "1. 统一评估基准：构建覆盖多场景的评测集，难点是标注成本。\n"
        "2. 跨域迁移机制：标准化中间表示，难点是语义对齐。\n"
        "3. 过程可解释模块：记录每一步决策依据，难点是信息压缩。\n"
        "## 四、推荐的下一步\n先在小规模数据上验证基准有效性。"
    )
    return MockLLM([fake_screen, fake_digest, fake_ideas], name="demo-mock")


# ---------------------------------------------------------------------------
# 侧边栏：模型配置
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 模型配置")

    # 从平台 / 本地 secrets 读取默认配置（部署后在 Settings → Secrets 里配）
    # 注意：不存在 secrets 文件时，直接访问 st.secrets 会抛异常，这里做安全兜底
    def _secret(name: str, default: str = "") -> str:
        try:
            return st.secrets.get(name, default)
        except Exception:
            return default

    _secret_provider = _secret("LLM_PROVIDER", "deepseek")
    _secret_key = _secret("LLM_API_KEY", "")
    _secret_base = _secret("LLM_BASE_URL", "")
    _secret_model = _secret("LLM_MODEL", "")

    demo_mode = st.toggle(
        "离线演示模式（无需 API Key）",
        value=False,
        help="开启后 LLM 部分用模拟响应，arXiv 检索仍是真实的，可用于先体验流程。",
    )

    provider_options = ["deepseek", "doubao", "custom"]
    _provider_index = (
        provider_options.index(_secret_provider)
        if _secret_provider in provider_options
        else 0
    )
    provider = st.selectbox(
        "模型厂商",
        options=provider_options,
        index=_provider_index,
        format_func= lambda x: {
            "deepseek": "DeepSeek",
            "doubao": "豆包（火山方舟）",
            "custom": "自定义 OpenAI 兼容接口",
        }[x],
        disabled=demo_mode,
    )

    presets = {
        "deepseek": ("https://api.deepseek.com", "deepseek-chat"),
        "doubao": ("https://ark.cn-beijing.volces.com/api/v3", ""),
        "custom": ("", ""),
    }
    preset_base, preset_model = presets[provider]

    # 输入框留空时，自动使用平台密钥；手动输入则覆盖
    api_key = st.text_input(
        "API Key（留空则用平台密钥）",
        type="password",
        placeholder="已在平台 Secrets 配置" if _secret_key else "sk-...",
        disabled=demo_mode,
        help="密钥只在会话内存中使用，不写磁盘。",
    )
    base_url = st.text_input(
        "Base URL",
        value=_secret_base or preset_base,
        disabled=demo_mode,
    )
    model_name = st.text_input(
        "模型名",
        value=_secret_model or preset_model,
        disabled=demo_mode,
        help="豆包请填推理接入点 ID（ep- 开头）。",
    )

    st.divider()
    st.caption("论文源：arXiv（免费，无需 Key）")
    st.caption("检索数据实时来自 arXiv API")

    # 构建客户端（失败时记录错误，主区提示）
    llm_client = None
    config_error = None
    if demo_mode:
        llm_client = make_demo_llm()
    else:
        # 界面输入优先；界面为空则回退到平台密钥
        final_key = api_key.strip() or _secret_key
        final_base = base_url.strip() or preset_base
        final_model = model_name.strip() or preset_model

        if final_key:
            try:
                from paper_agent.config import LLMConfig
                from paper_agent.llm import LLMClient

                llm_client = LLMClient(
                    LLMConfig(
                        api_key=final_key,
                        base_url=final_base,
                        model=final_model,
                        provider=provider,
                    )
                )
            except Exception as e:  # noqa: BLE001
                config_error = str(e)
        elif not _secret_key:
            config_error = None  # 下方主体会提示去配置


# ---------------------------------------------------------------------------
# 主体
# ---------------------------------------------------------------------------
st.markdown('<div class="main-title">📚 论文研究 Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">自动检索论文 · 结构化精读 · 提炼创新点与 Idea</div>',
    unsafe_allow_html=True,
)

if config_error:
    st.error(f"模型初始化失败：{config_error}")
elif llm_client is None:
    st.info("请在左侧填写 API Key，或打开「离线演示模式」先体验流程。")

tab_search, tab_pdf = st.tabs(["🔍 追前沿（联网检索）", "📄 精读 PDF"])


# 运行函数：统一处理进度展示、报告生成与结果保存
def run_task(task_callable, progress_placeholder) -> None:
    logs: list[str] = []

    def on_progress(message: str) -> None:
        logs.append(message)
        progress_placeholder.code("\n".join(logs), language="text")

    try:
        with st.spinner("Agent 正在工作，请稍候……"):
            result = task_callable(on_progress)
        report_text = build_report(result)
        report_path = save_report(result, out_dir=str(ROOT / "papers"))
        st.session_state["report_text"] = report_text
        st.session_state["report_path"] = report_path
        st.success(f"完成！报告已保存到 {report_path}")
    except Exception as e:  # noqa: BLE001
        st.error(f"运行失败：{type(e).__name__}: {e}")


# ===========================================================================
# Tab 1：联网检索
# ===========================================================================
with tab_search:
    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_input(
            "研究主题",
            value="AI Agent 的自主规划与工具调用",
            help="会作为报告标题，也用于相关性筛选。",
        )
        keywords_text = st.text_input(
            "检索关键词（多个用英文逗号分隔，建议用英文）",
            value="AI agent, tool use",
        )

    with col2:
        category_label = st.selectbox(
            "arXiv 分类",
            options=["不限"] + [f"{k}（{v}）" for k, v in CS_CATEGORIES.items() if k != "CL_"],
        )
        max_results = st.slider("候选论文数", 5, 30, 10, step=5)
        top_k = st.slider("最终精读篇数", 1, 8, 3, help="篇数越多，调用成本越高。")

    st.markdown(
        '<div class="hint">流程：检索 arXiv → 相关性筛选 → 逐篇精读 → 横向对比提炼 idea。'
        " 精读篇数越多耗时越长。</div>",
        unsafe_allow_html=True,
    )

    if st.button("开始检索并提炼 Idea", type="primary", disabled=llm_client is None):
        keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
        cat = None if category_label == "不限" else category_label.split("（")[1].rstrip("）")

        progress_box = st.empty()
        run_task(
            lambda on_progress: ResearchAgent(
                llm=llm_client, progress=on_progress
            ).search_and_ideate(
                topic=topic,
                keywords=keywords,
                category=cat,
                max_results=max_results,
                top_k=top_k,
            ),
            progress_box,
        )


# ===========================================================================
# Tab 2：PDF 精读
# ===========================================================================
with tab_pdf:
    uploaded = st.file_uploader(
        "上传论文 PDF（可多选）",
        type=["pdf"],
        accept_multiple_files=True,
        help="支持多篇一起上传做横向对比；扫描件需先 OCR。",
    )

    if st.button("开始精读", type="primary", disabled=llm_client is None):
        if not uploaded:
            st.warning("请先上传至少一个 PDF 文件。")
        else:
            # 把上传的文件写到临时目录，交给解析器读取
            tmp_paths: list[str] = []
            for f in uploaded:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(f.getbuffer())
                tmp.close()
                tmp_paths.append(tmp.name)

            progress_box = st.empty()
            run_task(
                lambda on_progress: ResearchAgent(
                    llm=llm_client, progress=on_progress
                ).analyze_pdfs(tmp_paths),
                progress_box,
            )


# ===========================================================================
# 结果展示（跨 Tab 共用）
# ===========================================================================
if "report_text" in st.session_state:
    st.divider()
    st.subheader("📑 研究报告")

    report_text: str = st.session_state["report_text"]
    report_path: str = st.session_state.get("report_path", "")

    st.download_button(
        "⬇️ 下载 Markdown 报告",
        data=report_text,
        file_name=pathlib.Path(report_path).name if report_path else "report.md",
        mime="text/markdown",
    )

    with st.expander("展开查看完整报告", expanded=True):
        st.markdown(report_text)
