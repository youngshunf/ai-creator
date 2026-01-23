## 目标与范围

- 新增桌面端「选题中心」完整功能：列表页 + 详情页。
- 公共选题：从云端 `sys_topic`（现有接口 `/topic/recommendations`）获取并展示。
- 私有选题：从云端 `project_topics`（现有接口 `/projects/{project_id}/topics`）获取并展示。
- 支持基于当前项目信息手动生成私有选题：调用 Tauri 命令 `generate_project_topics` → 可选触发 `start_sync` 推送到云端。

## UI/UX 设计（ui-ux-pro-max 风格落地）

- 视觉风格：SaaS 玻璃拟态 + 极简（沿用现有 `glass-card`、primary 蓝 + CTA 橙、Space Grotesk 标题/DM Sans 正文）。
- 信息架构：
  - 顶部：页面标题 + Tab（公共/私有）+ 搜索框 + 过滤器（行业/状态）+ 主 CTA（生成选题/同步）。
  - 列表区：卡片栅格（2~3 列自适应），每卡展示：标题、潜力分、热度、Top 标签、来源/趋势摘要、主操作「查看详情」。
  - 详情区：Bento Grid：
    - 左侧：核心指标（潜力/热度/趋势）、关键词、适配平台热度分布（Key-Value 或小条形）。
    - 右侧：推荐理由、创作角度、内容大纲、素材线索、风险提示（分组卡片）。
- 交互细节：
  - Skeleton/空状态/错误状态统一；
  - 所有可点击卡片 `cursor-pointer` + hover 阴影/描边；
  - 生成选题用对话框：进度状态、成功 toast、失败 toast。

## 数据获取与状态管理

- 使用 @tanstack/react-query（项目已引入但未广泛使用）来做：缓存、加载态、刷新。
- 公共选题：
  - `GET /topic/industries` 拉行业树（用于筛选，可选）。
  - `GET /topic/recommendations?industry_id&limit` 拉 sys topics。
  - 详情页：优先从 query cache 取；若 cache 缺失则 fallback 重新拉 recommendations（limit 提高）后按 id 定位。
- 私有选题：
  - 依赖 `currentProject.cloud_id` 作为云端 project_id。
  - 若 cloud_id 缺失：提示“请先同步项目到云端”。

## 需要补齐/调整的前端类型

- `useProjectStore` 的 `RawProject/Project` 增加 `cloud_id?: number`（与 Rust Project 新增字段对齐），确保同步拉回云端 id 后，前端可用于请求私有选题列表。

## 新增/修改的前端模块（拟）

- API 层：
  - `apps/desktop/src/api/topic.ts`：industries/recommendations。
  - `apps/desktop/src/api/projectTopic.ts`：getProjectTopics(projectId)。
- 路由：
  - `apps/desktop/src/routes/topics/index.tsx`：选题中心列表页（公共/私有 Tab）。
  - `apps/desktop/src/routes/topics/public/$id.tsx`：公共选题详情。
  - `apps/desktop/src/routes/topics/private/$uuid.tsx`：私有选题详情。
- 组件：
  - `apps/desktop/src/components/topics/TopicCard.tsx`
  - `apps/desktop/src/components/topics/TopicDetail.tsx`
  - `apps/desktop/src/components/topics/GenerateTopicsDialog.tsx`（输入 TrendRadar base_url 等；一键生成并可选同步）

## 手动生成私有选题（端侧）

- 列表页「生成选题」按钮：
  - 打开弹窗：TrendRadar base_url（必填）+ endpoint_path/payload_mode（可选，默认值与后端一致）。
  - 点击生成：invoke `generate_project_topics({ projectId, trendradarBaseUrl, ... })`。
  - 生成完成：立即刷新私有列表（react-query invalidate）；若已登录且有 token，顺带 invoke `start_sync` 让 pending 选题尽快 push 到云端。

## 验证与验收（实现后执行）

- 本地：打开桌面端，进入「选题中心」：
  - 公共 Tab 可加载列表/进入详情；
  - 私有 Tab 在已同步项目下可加载列表/进入详情；
  - 点击「生成选题」后能看到新选题进入列表，并在下一次同步后云端可见。
- 工程：`pnpm -C apps/desktop build` 与 `pnpm -C apps/desktop lint`（如已有规则）通过；`tauri dev` 可正常运行。

## 可选增强（不阻塞主功能）

- 后端补一个 sys_topic detail 接口 `GET /topic/topic/{id}`，避免详情页 fallback 拉大列表。
- 私有选题支持「采纳/忽略」状态切换并同步（对应 status=1/2）。
