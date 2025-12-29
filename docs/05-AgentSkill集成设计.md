# Agent Skill 集成设计方案 (Markdown 版)

**版本**: v1.1
**日期**: 2025-12-30

## 1. 核心变更

采用 **Markdown (.md)** 格式定义 Skill，以便于 Claude 直接阅读和理解。
结构采用 **YAML Frontmatter** + **Markdown Body**。

## 2. Skill 文件规范 (`.md`)

```markdown
---
name: academic-researcher
version: "1.0.0"
description: "学术研究技能，能够查找、阅读并总结学术论文。"
author: "CreatorFlow"
tags: ["research", "paper"]
tools:
  - arxiv_search
  - google_scholar_tool
requirements:
  - arxiv
---

# Expert Instructions

你现在拥有学术研究能力。请遵循以下原则进行操作：

1.  **优先使用 arXiv** 获取最新论文。
2.  如果 arXiv 未找到，尝试 Google Scholar。
3.  阅读论文时，重点关注 **Abstract** 和 **Conclusion**。

## Few-Shot Examples

### User
帮我找一下关于 RAG 的最新论文

### Assistant
<thought>
用户需要最新的 RAG 论文，我应该先搜索 arXiv。
</thought>
<tool_code>
arxiv_search(query="Retrieval-Augmented Generation", sort_by="submittedDate")
</tool_code>
```

## 3. 解析逻辑

`SkillLoader` 将执行以下解析：

1.  **Frontmatter**: 提取 `metadata` (name, version, etc) 和 `spec.tools`。
2.  **Body**: 将 Frontmatter 之后的所有内容作为 `spec.instructions` (包含 Examples)。
    *   *注*: 我们不再将 Examples 强制解析为结构化 JSON，而是作为 Prompt 的一部分直接注入。这更符合 LLM "In-Context Learning" 的本质，也简化了格式。

## 4. 目录结构

```text
agent-definitions/
└── skills/
    ├── academic-researcher.md
    ├── python-coder.md
    └── data-analyst.md
```
