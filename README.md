# Paper Research Assistant

一个面向 Codex 的本地论文库辅助 skill，用来检索本地 PDF 论文、生成带页码证据的回答、辅助论文精读、文献综述、论点核查，以及中英文学术润色。

它适合这样的工作流：

- “在我的论文库里找 hidden Markov model order estimation 相关论文，并按证据页码总结。”
- “精读这篇论文，整理模型、假设、估计方法、主要定理和局限。”
- “帮我检查这段论文表述有没有本地文献支持。”
- “润色这段英文/中文学术写作，但不要改变数学含义。”

## 仓库结构

```text
Paper-Research-Assistant/
├─ README.md
├─ .gitignore
└─ paper-research-assistant/
   ├─ SKILL.md
   ├─ agents/openai.yaml
   ├─ scripts/
   │  ├─ build_index.py
   │  └─ search_library.py
   ├─ references/
   │  ├─ citation-policy.md
   │  ├─ reading-protocol.md
   │  └─ polishing-rules.md
   ├─ assets/reading-note-template.md
   └─ data/.gitkeep
```

`paper-research-assistant/` 是真正的 Codex skill 目录。`data/library.sqlite3` 是本地生成的索引数据库，默认不会提交到 GitHub。

## 安装方式

把 `paper-research-assistant` 目录复制到你的 Codex skills 目录。

Windows PowerShell 示例：

```powershell
Copy-Item -Recurse -Force .\paper-research-assistant "$env:USERPROFILE\.codex\skills\paper-research-assistant"
```

macOS / Linux 示例：

```bash
mkdir -p ~/.codex/skills
cp -R ./paper-research-assistant ~/.codex/skills/paper-research-assistant
```

安装后，重新打开 Codex 或开启一个新对话，应该就能使用：

```text
使用 $paper-research-assistant 检索我的本地论文库并给出带页码的可靠回答。
```

## 准备论文库

这个 skill 不依赖 Zotero。你只需要准备一个文件夹，把 PDF 放进去即可，子文件夹可以按主题或年份组织。例如：

```text
D:\paper_reading_skills
├─ 统计理论/
├─ HMM与SSM/
└─ 深度状态空间模型/
```

添加新论文时，把 PDF 复制到这个文件夹或其子文件夹下，然后重新建立或增量更新索引。

## 建立索引

进入 skill 目录后运行：

```powershell
python .\scripts\build_index.py --library "D:\paper_reading_skills" --index .\data\library.sqlite3
```

如果只是新增了 PDF，且没有移动、删除、重命名或替换旧文件，可以用增量模式：

```powershell
python .\scripts\build_index.py --library "D:\paper_reading_skills" --index .\data\library.sqlite3 --resume
```

如果你移动、删除、重命名或替换了 PDF，请不要用 `--resume`，直接全量重建索引，避免索引里的路径过期。

脚本会：

- 递归扫描论文库中的 PDF；
- 用 SHA-256 去重，避免重复论文反复入库；
- 按 PDF 页码抽取文本并切块；
- 写入 SQLite FTS5 全文索引；
- 报告可能需要 OCR 的扫描版 PDF。

## 手动检索测试

```powershell
python .\scripts\search_library.py --index .\data\library.sqlite3 --query "variational sequential Monte Carlo" --limit 8
```

输出是 UTF-8 JSON，包含标题、作者、年份、文件路径、PDF 页码、文本片段和排序分数。

## 在 Codex 中使用

常用提示词示例：

```text
使用 $paper-research-assistant，在 D:\paper_reading_skills 中建立索引。
```

```text
使用 $paper-research-assistant，检索 hidden Markov model asymptotic normality，并按论文、页码和结论整理。
```

```text
使用 $paper-research-assistant，精读这篇论文，输出研究问题、模型假设、估计方法、主要结果、局限和可借鉴点。
```

```text
使用 $paper-research-assistant，润色下面这段英文论文表述，保持数学含义和引用键不变。
```

## 证据与引用原则

这个 skill 的核心原则是：只根据本地论文库中检索到并检查过的段落回答。

- 不编造标题、作者、年份、DOI、页码或直接引文；
- 区分论文原文明确陈述和基于多段证据的推断；
- 对重要结论给出 `[论文标题, PDF p. N]`；
- 如果检索结果不能支持某个说法，应明确写出“论文库中未找到充分证据”；
- PDF 页码默认指物理 PDF 页码，不等同于论文印刷页码。

## 隐私说明

不要把本地生成的 `data/library.sqlite3` 上传到公开仓库。它可能包含：

- 论文全文抽取片段；
- 你的本地文件路径；
- 论文库组织方式。

本仓库的 `.gitignore` 已经排除了常见 SQLite 索引文件。

## 依赖

索引脚本需要 Python 3 和 `pypdf`。在 Codex 桌面环境中，通常可以使用 Codex 自带的 Python 运行时；如果在普通终端里运行，请先安装：

```bash
pip install pypdf
```

## 限制

- 扫描版 PDF 或图片型 PDF 需要先做 OCR；
- PDF 元数据可能不完整，标题、作者和年份以可抽取信息为准；
- 检索结果是辅助阅读入口，不应替代人工核对原文；
- 脚本目前使用 SQLite FTS5，不是向量数据库，复杂语义检索需要通过关键词改写来提高召回。

## License

如果你希望公开给别人复用，建议在仓库中补充一个开源许可证，例如 MIT License。
