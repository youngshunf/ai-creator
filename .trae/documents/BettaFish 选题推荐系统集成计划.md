# BettaFish 选题推荐系统集成计划 (V2)

根据您的反馈，我们对数据库模型进行了深度扩展，增加了行业分类管理，并完善了选题的详细指标字段，以匹配 UI 设计图的要求。

## 1. 核心变更点

- **新增行业管理 (`Industry`)**：支持主行业、子行业层级结构，并预设行业关键词，用于精准抓取热点。
- **扩展选题模型 (`Topic`)**：完全匹配 UI 卡片展示需求，包含潜力分、热度指数、平台热度分布、多维度标签等。
- **数据初始化**：预置全行业分类数据，确保系统启动即用。

## 2. 详细实施步骤

### 2.1 数据库模型设计

**文件位置**: `services/cloud-backend/backend/app/topic/model/topic.py`

#### A. 行业表 (`sys_industry`)

用于定义爬虫和分析的关注领域。

- `id`: 主键
- `name`: 行业名称 (如 "美妆", "AI绘画")
- `parent_id`: 父级ID (支持主行业/子行业树形结构)
- `keywords`: 行业关键词 (JSON数组，如 `["眼影", "口红", "修容"]`)，用于舆情搜索
- `description`: 描述
- `sort`: 排序字段

#### B. 选题表 (`sys_topic`)

用于存储每日生成的推荐选题。

- `id`: 主键
- `title`: **选题标题** (如 "新年妆容趋势：如何用国货打造高级感")
- `industry_id`: 关联子行业 ID
- `potential_score`: **选题潜力分数** (0-100，如 92)
- `heat_index`: **热度指数** (0-100，如 85)
- `reason`: **推荐理由/洞察** (如 "结合春节热门话题和国货美妆热潮...")
- `keywords`: **标签/关键词** (JSON数组，如 `["美妆", "国货", "新年", "教程"]`)
- `platform_heat`: **平台热度** (JSON对象，存储各平台热度值，如 `{"小红书": 90, "抖音": 80, "B站": 60}`)
- `source_info`: 来源信息 (JSON对象，记录原始热点链接或来源话题)
- `status`: 状态 (0: 待选, 1: 已采纳, 2: 已忽略)
- `created_at`: 创建时间

### 2.2 初始化数据生成

**文件位置**: `services/cloud-backend/backend/app/topic/crud/init_data.py`
我们将预置以下行业结构（部分示例）：

- **科技**: AI (关键词: ChatGPT, Midjourney), 数码 (手机, 电脑)
- **美妆**: 彩妆 (眼妆, 底妆), 护肤 (成分, 抗老)
- **美食**: 探店, 食谱 (减脂餐, 早餐)
- **生活**: 家居, 宠物, 职场
- **财经**: 理财, 基金
  （将生成完整的 SQL 或代码插入逻辑，覆盖 50+ 子行业）

### 2.3 业务逻辑实现 (`TopicService`)

**文件位置**: `services/cloud-backend/backend/app/topic/service/topic_service.py`

1.  **`generate_daily_topics()`**:
    - 遍历 `sys_industry` 表中的活跃子行业。
    - 利用行业 `keywords` 调用 BettaFish API 获取实时热点。
    - **数据清洗与增强**:
      - 计算 `potential_score` (基于热度趋势、竞争度)。
      - 生成 `platform_heat` 分布数据。
      - 提取/生成 `keywords` 标签。
      - 生成 `reason` 推荐语。
    - 存入 `sys_topic` 表。

2.  **`get_recommended_topics(query)`**:
    - 支持按行业、热度、潜力分排序筛选。
    - 返回格式直接适配前端卡片组件。

### 2.4 定时任务与 API

- **定时任务**: `backend/app/topic/tasks/tasks.py` -> 每日凌晨 2:00 执行全量生成。
- **API**:
  - `GET /api/v1/topic/industries`: 获取行业树。
  - `GET /api/v1/topic/recommendations`: 获取推荐选题列表。
  - `POST /api/v1/topic/{id}/adopt`: 采纳选题（通过 ID 关联到创作工作流）。

## 3. 下一步行动

确认计划后，我将按顺序执行：

1.  创建目录结构与数据库模型代码。
2.  编写行业初始化数据脚本。
3.  实现 Service 核心逻辑与 API。
