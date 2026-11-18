# 论文研究 Agent（Paper Research Agent）

一个专门帮你**看论文、追前沿、提炼创新点和 idea** 的智能体。它会自动检索
arXiv 最新论文、精读你上传的 PDF，做结构化归纳，再通过横向对比产出可落地的
研究 idea，并生成**带引用链接、可追溯**的 Markdown 报告。

- 研究方向：计算机 / AI / 电子信息（arXiv 全部分类）
- 模型：国产大模型（DeepSeek / 豆包，OpenAI 兼容接口），可自行替换
- 论文来源：联网检索 + 上传 PDF 两种方式都支持
- **使用方式：网页界面（在 Edge 浏览器打开，Windows 双击即可启动）**；也保留命令行版
- 已在云主机验证，可直接运行，也可迁移到本地

> 📱 **想在安卓手机上像 App 一样用？** 按 [`手机部署指南.md`](手机部署指南.md)
> 操作：免费部署到云端后，在手机「添加到主屏幕」即可，无需应用商店。

---

## 一、它能做什么

**联网模式**：给一个研究主题和关键词，它自动完成

```
检索 arXiv 最新论文 → 大模型相关性筛选 → 逐篇精读归纳
→ 横向对比找研究空白 → 产出候选 idea（含做法/依据/难点）→ 生成报告
```

**PDF 模式**：给它论文 PDF，它自动

```
解析文本 → 长文分块（map-reduce 精读，支持超长论文）
→ 结构化笔记 → 提炼可延展方向和 idea → 生成报告
```

每篇论文都会保留摘要页和 PDF 链接，报告里每个结论都能追溯到来源。

---

## 二、项目结构

```
paper_research_agent/
├── README.md                 # 本文档
├── 手机部署指南.md            # ⭐ 安卓手机"安装"到桌面的分步指南
├── requirements.txt          # 依赖
├── .env.example              # 配置模板（复制为 .env 填 key）
├── .gitignore                # 保护密钥与本地产物
├── app.py                    # ⭐ 网页界面（Streamlit，含 PWA 注入）
├── make_icons.py             # 生成 PWA 图标（PIL）
├── 启动程序.bat              # ⭐ Windows 一键启动（双击即可）
├── start.sh                  # macOS / Linux 启动脚本
├── start_public.sh           # 可选：Cloudflare 临时隧道（手机零配置体验）
├── .streamlit/
│   ├── config.toml           # 开启静态服务、主题色
│   └── secrets.toml.example  # 平台密钥模板（真实文件勿提交）
├── static/                   # PWA 资源（manifest + 图标）
│   ├── manifest.json
│   ├── icon-192.png
│   ├── icon-512.png
│   └── icon-512-maskable.png
├── paper_agent/
│   ├── config.py             # 配置加载（DeepSeek/豆包预设）
│   ├── llm.py                # 真实客户端 + 离线 MockLLM
│   ├── arxiv_client.py       # arXiv 检索（免费、无需 key）
│   ├── pdf_reader.py         # PDF 解析与分块
│   ├── prompts.py            # 筛选/精读/idea 各环节提示词
│   ├── research_agent.py     # 研究主流程（联网 + PDF）
│   └── report.py             # Markdown 报告生成
├── examples/
│   ├── run_search.py         # 联网检索示例（命令行）
│   └── run_pdf.py            # PDF 精读示例（命令行）
├── tools/                    # cloudflared 二进制（不提交 GitHub）
├── logs/                     # 隧道运行日志（不提交 GitHub）
└── papers/                   # 报告与测试 PDF 输出目录
```

---

## 三、安装

```bash
# 要求 Python 3.10+
python3 --version

# 安装依赖
pip install -r requirements.txt
```

---

## 四、配置大模型 API Key（关键步骤）

**1. 申请 API Key（二选一）**

- DeepSeek：访问 `https://platform.deepseek.com`，注册后在「API keys」创建，
  复制 `sk-` 开头的密钥；
- 豆包：访问火山引擎控制台，开通「方舟」服务，创建推理接入点，获取 API Key
  和接入点 ID（`ep-` 开头）。

**2. 配置 .env**

```bash
# 复制模板
cp .env.example .env
```

编辑 `.env`，填入真实密钥。DeepSeek 示例：

```ini
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-你的真实key
```

豆包示例：

```ini
LLM_PROVIDER=doubao
LLM_API_KEY=你的火山引擎key
LLM_MODEL=ep-你的接入点ID
```

> 密钥只保存在你本地的 `.env` 文件中，注意不要把 `.env` 分享或提交到公开仓库。

---

## 五、网页版使用（推荐，在 Edge 打开）

这是最省事的方式：双击启动，浏览器里点按操作，能直接上传 PDF。

### Windows 用户（最简单）

**双击 `启动程序.bat`**。脚本会自动完成：检查 Python → 首次运行自动装依赖 →
启动服务 → 用 **Edge 的"应用模式"**打开窗口（没有地址栏和标签栏，看起来就像
一个独立软件）。

> 使用期间不要关闭那个黑色命令行窗口，关闭它会停止服务。

若窗口没自动弹出，手动打开 Edge 访问 `http://localhost:8501`。

### macOS / Linux 用户

```bash
chmod +x start.sh
./start.sh
```

然后在浏览器打开 `http://localhost:8501`。

### 手动启动（任意系统）

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

终端会打印访问地址，用 Edge 打开即可。

### 网页界面怎么用

1. **左侧栏**填写 API Key（只在本次会话内存里使用，不写磁盘）。只想先体验流程，
   打开「**离线演示模式**」就不用 Key——arXiv 检索仍是真实的，只是模型回答用模拟；
2. **「追前沿」** 标签页：填研究主题、关键词（英文逗号分隔），选 arXiv 分类，
   拖动滑杆定候选数和精读篇数，点「开始检索并提炼 Idea」，页面会**实时显示进度**；
3. **「精读 PDF」** 标签页：把论文 PDF 拖进去（可多选，能横向对比），点「开始精读」；
4. 跑完后页面下方出现完整报告，**可直接阅读**，也能点「下载 Markdown 报告」保存。

### 想更像"电脑软件"？

- **已实现**：启动脚本用 Edge 应用模式打开，窗口无地址栏，观感接近独立软件；
- **可进一步打包成 exe**：若你需要一个能发给别人、对方双击即用的 exe，可用
  `pyinstaller` / `pywebview` 封装。打包对运行环境影响较大，需要时告诉我，
  我再给你做一份带打包脚本的版本。

---

## 六、命令行使用（进阶 / 批量）

适合放进定时脚本，或你更习惯终端操作。

### 1) 联网检索，自动找 idea（真实模式）

先编辑 `examples/run_search.py` 顶部的研究主题和关键词：

```python
TOPIC = "AI Agent 的自主规划与工具调用"
KEYWORDS = ["AI agent", "tool use"]
CATEGORY = "AI"        # AI=cs.AI，LG=cs.LG，CL=cs.CL，CV=cs.CV，None=不限
```

然后运行：

```bash
python examples/run_search.py
```

### 2) 精读 PDF（真实模式）

```bash
python examples/run_pdf.py /path/to/你的论文.pdf
```

可一次传多篇，在代码里把路径加入列表即可做横向对比。

### 3) 离线演示（无需 Key，先验证流程）

```bash
python examples/run_search.py --mock    # arXiv 真实检索，LLM 用脚本模拟
python examples/run_pdf.py --mock       # 自动生成测试 PDF 并精读
```

报告统一输出到 `papers/` 目录，文件名带时间戳。

---

## 七、如何改成你自己的研究方向

只需要改 `examples/run_search.py` 里的三个变量：

| 参数 | 含义 | 示例 |
|---|---|---|
| `TOPIC` | 研究主题（也是报告标题） | `"面向边缘设备的轻量化大模型推理"` |
| `KEYWORDS` | 检索关键词列表 | `["model compression", "edge inference"]` |
| `CATEGORY` | arXiv 分类 | `"LG"` / `"CV"` / `None`（不限） |
| `max_results` | 候选论文数量 | `20` |
| `top_k` | 最终精读篇数 | `5` |

想调整 idea 的风格（更偏理论 / 更偏工程），可修改 `paper_agent/prompts.py`
中 `IDEA_PROMPT` 的要求。

---

## 八、工作原理（对应吴恩达 Agentic AI 课程）

本项目是课程"深度研究 Agent"的落地，用到的核心模式：

- **工具使用**：模型只输出检索/读取意图，arXiv 调用和 PDF 解析都在 Python 侧执行；
- **规划**：研究流程拆成检索、筛选、精读、idea 等可验收步骤；
- **反思/评估**：每个环节有明确产出，报告引用可被程序核对；
- **map-reduce 精读**：长论文分块总结再合并，突破单次上下文长度限制。

---

## 九、常见问题

**Q：运行报 `未检测到 LLM_API_KEY`？**
A：说明没配置 `.env`，或 key 没填对。先按第四节配置；只想看流程可加 `--mock`；
网页版则打开左侧的「离线演示模式」。

**Q：双击 `启动程序.bat` 一闪就没了？**
A：多半是没装 Python 或安装时没勾选 "Add Python to PATH"。重新安装 Python 3.10+
并勾选该选项后重试；也可在命令行里运行该 bat 查看具体报错。

**Q：检索不到论文？**
A：换更通用的英文关键词（arXiv 标题/摘要以英文为主），或把 `CATEGORY` 设为 `None`。

**Q：PDF 提示需要 OCR？**
A：该 PDF 是扫描件、没有文本层，需要先用 OCR 工具（如 tesseract）转换。

**Q：想用其他模型（OpenAI/Claude/本地 Ollama）？**
A：在 `.env` 设 `LLM_PROVIDER=custom`，并填写对应的 `LLM_BASE_URL` 和 `LLM_MODEL`，
只要是 OpenAI 兼容接口即可，其余代码不变。

**Q：费用如何？**
A：arXiv 检索免费；费用只来自大模型调用，精读篇数越多、论文越长，调用量越大。
可先调小 `top_k` 控制成本。
