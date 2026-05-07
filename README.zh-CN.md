# papersearch

🌐 [English](README.md) | [简体中文](README.zh-CN.md)

papersearch 是一个面向 Claude Code 的论文研究 Skill。

它可以帮你：
- 按主题、会议或年份找论文
- 快速判断一篇论文值不值得读
- 对单篇论文做深度分析
- 生成适合 Obsidian / Zotero 的笔记

## 怎么用

直接用自然语言说你的需求即可，Claude 会自动路由。

### 1) 找一批论文

可以直接说：

- `帮我找 2024 ICLR 上 diffusion policy 的论文，优先有代码和项目链接`
- `给我整理一份 2023-2025 年 VLA 方向的 related work 列表`

你会得到：排序后的论文列表、匹配理由、筛选条件，以及本地语料覆盖情况。

### 2) 快速看一篇论文

可以直接说：

- `快速看这篇论文：arXiv 2401.12345`
- `这个 alphaXiv 链接值不值得读：https://www.alphaxiv.org/...`

你会得到：问题、核心方法、关键结果、局限，以及是否建议继续精读。

### 3) 深度调研一篇论文

可以直接说：

- `深度分析这篇论文的方法、实验设计和局限`
- `把这篇论文和 XXX baseline 对比，并给出结论`

你会得到：结构化深度分析，以及后续值得追问的重点。

### 4) 输出可归档文档

如果你要进入高级工作流，请明确说出 `保存`、`归档`、`Obsidian`、`Zotero` 或 `批处理`。

可以直接说：

- `读这篇论文并输出 Obsidian 笔记，包含关键图表和公式说明`
- `处理这个 Zotero 分类，批量生成论文笔记并归档`

你会得到：可归档笔记、工作流输出、以及批处理状态。

## 常见问题

### 这个 skill 只有“搜论文”吗？
不是。它也支持单篇速读、深度调研，以及 Obsidian / Zotero 归档输出。

### 我需要手动指定 search/lookup/reader 吗？
不需要。直接说目标即可。

## 本地调试

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

示例：

```bash
./scripts/run.sh search "find 2024 iclr papers about diffusion policy with code"
./scripts/run.sh lookup "2401.12345" --format brief
./scripts/run.sh reader --status
```

## 环境要求

- Python 3.10+
- macOS / Linux
