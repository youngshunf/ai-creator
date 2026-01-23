# 选题推荐系统（系统库 + 用户私有库 + TrendRadar + LLM网关）Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 每天基于行业/关键词聚合多平台热点，并生成“可直接入库”的选题卡片：

- 云侧：`sys_industry → sys_topic`（系统选题库，定时）
- 端侧：`projects → project_topics`（用户私有选题库，本地生成，可同步到云端）
- LLM：端云一致通过统一 LLM 网关调用

**Architecture:** “热点抓取/归一化 + LLM 结构化卡片生成”实现在 `agent-core`；云端负责系统库落库与定时；桌面端负责私有库落库与同步。

---

## 强约束（根据你最新要求补齐）

### sys_topic 表字段必须全部入库

- 生成链路必须保证：`sys_topic` 的每个字段在写入时都有值（即使是空结构）。
- 具体策略：
  - 文本/数值字段：`title` 必填；`potential_score/heat_index` 必填（0-100）；`reason` 必填（至少给出简短理由）。
  - JSONB 字段：全部写入，若无信息则写空数组/空对象：
    - `keywords` / `heat_sources` / `industry_tags` / `target_audience` / `creative_angles` / `content_outline` / `format_suggestions` / `material_clues` / `risk_notes`：默认 `[]`
    - `platform_heat` / `trend` / `source_info`：默认 `{}`
  - `status`：默认 `0`。

---

## 交付物：设计文档（保存到 docs/）

### Task 0: 写入设计文档

**Files:**

- Create: `docs/选题推荐系统-设计.md`

**内容必须包含：**

- sys_topic 字段全量映射表（字段→来源→默认值）
- project_topics 字段映射与同步策略

---

## agent-core：可复用的选题推荐引擎

### Task 1: 领域模型与引擎入口

**Files:**

- Create: `packages/agent-core/src/agent_core/topic_recommender/models.py`
- Create: `packages/agent-core/src/agent_core/topic_recommender/recommender.py`
- Modify: `packages/agent-core/src/agent_core/__init__.py`

**模型要求：**

- `TopicCard` 必须包含 sys_topic 的全字段（除 ORM 元字段），并带 `ensure_defaults()` 方法填充空结构默认值。

### Task 2: TrendRadar Provider（含降级）

**Files:**

- Create: `packages/agent-core/src/agent_core/topic_recommender/providers/trendradar.py`
- Create: `packages/agent-core/src/agent_core/topic_recommender/providers/newsnow.py`

### Task 3: LLM Analyzer（统一网关，输出全字段 JSON）

**Files:**

- Create: `packages/agent-core/src/agent_core/topic_recommender/analyzers/llm_topic_card.py`

**Prompt / JSON Schema（严格约束）：**

- 输出必须为：
  - `topics: TopicCard[]`
  - 且每个 TopicCard 含下列字段（全部 required）：
    - `title, potential_score, heat_index, reason`
    - `keywords, platform_heat, heat_sources, trend`
    - `industry_tags, target_audience`
    - `creative_angles, content_outline, format_suggestions, material_clues, risk_notes`
    - `source_info`
- 解析后统一调用 `TopicCard.ensure_defaults()`，保证任何缺失字段都补齐为约定默认值。

### Task 4: agent-core 单测（覆盖“全字段落地”）

**Files:**

- Create: `packages/agent-core/tests/topic_recommender/test_llm_analyzer_parse.py`

**新增断言：**

- 任何生成的 `TopicCard` 都包含并填充所有 sys_topic 字段（无 None）。

---

## 云端：系统选题库（sys_industry → sys_topic，每日定时）

### Task 5: 用 agent-core 重写 generate_daily_topics（全字段写入）

**Files:**

- Modify: `services/cloud-backend/backend/app/topic/service/topic_service.py`

**实现硬要求：**

- 创建 `Topic(...)` 时显式为 sys_topic 每个字段赋值（包括 JSONB 空结构）。
- `source_info` 必须入库：至少包含 provider 名、输入关键词、原始热点列表（可截断）与 LLM 输出摘要。

### Task 6: sys_topic 幂等字段（推荐新增）

**Files:**

- Create: `services/cloud-backend/backend/alembic/versions/<new>_add_sys_topic_batch_fields.py`
- Modify: `services/cloud-backend/backend/app/topic/model/topic.py`

### Task 7: Celery Beat 每日调度

**Files（二选一）：**

- Modify: `services/cloud-backend/backend/app/task/tasks/beat.py`
  或
- Modify: `services/cloud-backend/backend/app/task/service/scheduler_service.py`

---

## 云端：用户私有选题库（project_topics，项目关联 + 同步）

### Task 8: 新增云端 ProjectTopic（字段对齐 sys_topic 全量字段）

**Files:**

- Create: `services/cloud-backend/backend/app/project/model/project_topic.py`
- Create: `services/cloud-backend/backend/alembic/versions/<new>_add_project_topics.py`

**要求：**

- project_topics 必须包含与 sys_topic 同口径的全字段（再加 project_id/server_version/batch_date/source_uid）。

### Task 9: 云端 API：list + sync_upsert

**Files:**

- Create: `services/cloud-backend/backend/app/project/api/v1/project_topic.py`
- Modify: `services/cloud-backend/backend/app/project/api/router.py`
- Create: `services/cloud-backend/backend/app/project/schema/project_topic.py`
- Create: `services/cloud-backend/backend/app/project/crud/crud_project_topic.py`
- Create: `services/cloud-backend/backend/app/project/service/project_topic_service.py`

---

## 桌面端：用户私有选题表（本地落库 + 同步）

### Task 10: 新增本地 SQLite 表 project_topics（payload 存全字段 JSON）

**Files:**

- Modify: `apps/desktop/src-tauri/src/db/schema.sql`
- Modify: `apps/desktop/src-tauri/src/db/repository.rs`

### Task 11: 生成入口：projects → Sidecar(agent-core) → project_topics

**Files:**

- Modify: `apps/desktop/src-tauri/src/commands/mod.rs`
- Modify: `apps/sidecar/src/sidecar/main.py`

---

## 桌面同步：project_topics ↔ 云端 project_topics

### Task 12: 增加 ProjectTopicProvider（pull + push）

**Files:**

- Create: `apps/desktop/src-tauri/src/sync/providers/project_topic.rs`
- Modify: `apps/desktop/src-tauri/src/sync/providers/mod.rs`
- Modify: `apps/desktop/src-tauri/src/sync/api_client.rs`
- Modify: `apps/desktop/src-tauri/src/lib.rs`

---

## 验证与验收

### Task 13: 云端验收

- 运行一次系统生成：确认 sys_topic 每条记录所有字段都已写入（JSONB 非空结构、数值/文本完整）。
- 重跑同日任务：确认幂等无重复。

### Task 14: 桌面端验收

- 生成私有选题：本地 project_topics 入库 payload 含全字段。
- start_sync：push 到云端，再 pull 回来一致。
