# 实施计划：MVP 功能开发 (离线优先模式)

根据需求文档，我将重构前端逻辑，使其优先使用本地 SQLite 数据库进行项目和账号管理，实现"离线优先"的架构。

## 1. 项目管理重构 (`useProjectStore.ts`)

- **目标**：从"云端 API 优先"切换为"本地 Tauri 命令优先"。
- **行动**：
  - 定义 `RawProject` 接口以匹配 Rust 后端的数据库模型（ID 为 UUID 字符串，列表字段为 JSON 字符串）。
  - 更新主 `Project` 接口，使用 `string` 类型作为 ID，并使用数组类型（如 `topics: string[]`）作为列表字段。
  - 创建辅助函数 `mapRawToProject`，用于将 SQLite 返回的 JSON 字符串解析为前端可用的数组。
  - 重写 `fetchProjects`：调用 `invoke('db_list_projects')` 获取本地数据。
  - 重写 `createProject`：调用 `invoke('db_create_project')` 写入本地数据库。
  - 重写 `updateProject` 和 `deleteProject` 以使用对应的本地 DB 命令。
  - 移除核心操作对 `api/project.ts` 的直接依赖，改为后台同步。

## 2. 账号管理重构 (`useAccountStore.ts`)

- **目标**：确保账号创建和列表功能的离线可用性。
- **行动**：
  - 验证 `PlatformAccount` 接口与 Rust `db_list_accounts` 返回的数据结构一致。
  - 确保 `addAccount` 在尝试云端同步之前，严格优先调用 `db_create_account` 进行本地存储。
  - 整合同步逻辑，确保本地变更后触发同步。

## 3. UI 适配更新

- **目标**：适配数据结构变更（主要是 ID 类型）。
- **行动**：
  - 更新 `ProjectSelector.tsx` 和 `project.create.tsx`，适配字符串类型的 UUID（原为数字 ID）。
  - 确保所有使用 `Project` 或 `Account` 对象的组件类型安全。

## 4. 同步逻辑 (基础)

- **目标**：建立本地数据库与云端的连接桥梁。
- **行动**：
  - 在 Store 中添加基础的 `syncProjectToCloud` 方法，确保在联网状态下本地数据能同步至服务器。

该计划将确保桌面端应用以本地 SQLite 为单一数据源，解决"项目和账号信息未保存到本地"的问题，并补全 MVP 所需的完整功能。
