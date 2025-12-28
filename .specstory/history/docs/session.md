# Session 记录

---

## 2025-12-28 LLM统一接口设计与文档更新

**时间**: 2025-12-28
**模型**: Claude Opus 4.5 (claude-opus-4-5-20251101)
**任务**: 更新LLM相关设计文档和桌面端开发计划

### 任务背景

用户需求:
- 云端LLM网关已完成开发，桌面端只需调用
- 将LLM调用能力集成到agent-core
- agent-core调用云端LLM网关，桌面端只需调用agent即可
- 云端可直接通过SDK调用网关
- LLM调用需提供统一接口，云端和桌面端实现不一致
- **桌面端不需要用户手动配置LLM，登录后自动分发API Token**
- **每个用户有独立的API Token**

### 执行步骤

#### 1. 文档阅读与分析

读取以下文档:
- `docs/04-云端服务设计.md` - 了解LLM网关设计
- `docs/15-桌面端开发计划.md` - 了解桌面端开发计划
- `docs/05-Agent-Runtime.md` - 了解Agent Runtime架构

#### 2. LLM统一接口架构设计

设计核心组件:
- `LLMClientInterface` - 统一调用接口
- `CloudLLMClient` - 桌面端HTTP调用实现
- `DirectLLMClient` - 云端直接SDK调用实现
- `LLMConfigManager` - 配置管理（自动保存Token）

#### 3. 文档更新

##### 3.1 Agent-Runtime.md (05-Agent-Runtime.md)

新增第10节 "LLM统一接口设计":
- 10.1 设计理念 - 统一接口架构图
- 10.2 接口定义 - LLMClientInterface
- 10.3 桌面端实现 - CloudLLMClient
- 10.4 云端实现 - DirectLLMClient
- 10.5 配置管理 - LLMConfigManager (简化版，自动Token管理)
- 10.6 桌面端配置文件示例 (自动生成)
- 10.7 登录流程集成 - 登录后自动获取Token
- 10.8 工具层集成
- 10.9 运行时上下文更新
- 10.10 端侧执行器初始化示例
- 10.11 云端执行器初始化示例
- 10.12 agent-core包结构更新

##### 3.2 云端服务设计.md (04-云端服务设计.md)

新增2.8节 "桌面端调用方式":
- 2.8.1 调用架构
- 2.8.2 API Token获取与认证
- 2.8.3 OpenAI兼容接口
- 2.8.4 桌面端配置文件 (自动生成)
- 2.8.5 Token分发流程

##### 3.3 桌面端开发计划.md (15-桌面端开发计划.md)

更新Sprint 2.2任务 (简化版):

| 任务 | 优先级 | 工时 | 交付物 |
|------|--------|------|--------|
| CloudLLMClient 实现 | P0 | 2d | LLM调用客户端 |
| LLMConfigManager 实现 | P0 | 1d | Token自动保存 |
| 登录流程集成 | P0 | 1d | Token分发 |
| 模型列表展示 | P1 | 1d | 模型选择 |
| 用量统计展示 | P1 | 1d | 用量追踪 |
| 连接状态检测 | P1 | 1d | 健康检查 |

### 关键设计决策

1. **统一接口**: 定义`LLMClientInterface`抽象接口，端云实现不同但接口一致
2. **自动Token分发**: 用户登录后自动获取API Token，无需手动配置
3. **Token格式**: `sk-cf-{user_id_hash}_{random_suffix}`
4. **简化配置**: 桌面端用户无需配置任何LLM相关设置
5. **OpenAI兼容**: 云端提供OpenAI兼容API，桌面端直接调用

### Token分发流程

```
用户登录 → 云端验证身份 → 返回JWT Token
                          ↓
桌面端调用 /api/v1/auth/llm-token
                          ↓
云端生成/返回独立API Token (sk-cf-xxx)
                          ↓
桌面端自动保存Token到本地配置
                          ↓
后续LLM调用自动携带Token
```

### 文件修改记录

| 文件 | 修改内容 | 修改人 | 时间 |
|------|---------|--------|------|
| docs/05-Agent-Runtime.md | 新增第10节LLM统一接口设计 | @Ysf | 2025-12-28 |
| docs/04-云端服务设计.md | 新增2.8节桌面端调用方式 | @Ysf | 2025-12-28 |
| docs/15-桌面端开发计划.md | 更新Sprint 2.2任务，版本v1.0→v1.1 | @Ysf | 2025-12-28 |

### 后续任务

桌面端开发时需实现:
1. `packages/agent-core/src/agent_core/llm/` 目录下的统一接口代码
2. `apps/sidecar/` 中集成CloudLLMClient和登录流程
3. 云端 `/api/v1/auth/llm-token` 接口

---

## 2025-12-28 15:37:33 - Agent Runtime 开发实现

**时间**: 2025-12-28 15:37:33
**模型**: Claude Opus 4.5 (claude-opus-4-5-20251101)
**任务**: 根据 docs/05-Agent-Runtime.md 完成 agent-runtime 的开发

### 任务概述

根据设计文档完成 Agent Runtime 的代码实现，包括：
- agent-core LLM 模块
- Sidecar JSON-RPC 服务
- 本地浏览器和凭证工具
- 云端 Agent 执行器
- 智能路由器

### 开发内容

#### 1. agent-core LLM 模块完善 ✅

**新增文件：**
- `packages/agent-core/src/agent_core/llm/config.py` - LLM 配置管理器
- `packages/agent-core/src/agent_core/llm/cloud_client.py` - 云端 LLM 客户端（HTTP 调用）
- `packages/agent-core/src/agent_core/llm/direct_client.py` - 直接调用 LLM 客户端
- `packages/agent-core/src/agent_core/llm/__init__.py` - 模块导出

**功能说明：**
- `LLMConfigManager`: 管理 LLM 配置，支持 Token 保存/加载/清除
- `CloudLLMClient`: 桌面端使用，通过 HTTP 调用云端 LLM 网关
- `DirectLLMClient`: 云端服务使用，直接调用 LLMGateway 实例

#### 2. Sidecar JSON-RPC 服务入口 ✅

**更新文件：**
- `apps/sidecar/src/sidecar/main.py` - JSON-RPC 服务主入口

**功能说明：**
- 实现 JSON-RPC 2.0 协议
- 支持方法：initialize, execute_graph, execute_graph_stream, list_graphs, health_check, login, logout, get_models, shutdown
- 通过 stdin/stdout 与 Tauri 进行通信

#### 3. Sidecar 本地浏览器和凭证工具 ✅

**更新文件：**
- `apps/sidecar/src/sidecar/tools/browser.py` - 本地浏览器工具
- `apps/sidecar/src/sidecar/tools/credential.py` - 本地凭证管理工具

**功能说明：**
- `LocalBrowserPublishTool`: 使用 Playwright 执行本地浏览器发布
- `LocalBrowserScrapeTool`: 使用 Playwright 执行数据采集
- `LocalCredentialTool`: 安全存储和管理平台凭证（AES-256-GCM 加密）

#### 4. 云端 Agent 执行器 ✅

**新增文件：**
- `apps/cloud-backend/backend/app/agent/__init__.py` - Agent 模块
- `apps/cloud-backend/backend/app/agent/executor.py` - 云端执行器
- `apps/cloud-backend/backend/app/agent/tools/__init__.py` - 云端工具模块
- `apps/cloud-backend/backend/app/agent/tools/browser.py` - 云端浏览器工具

**功能说明：**
- `CloudExecutor`: 云端 Graph 执行器，支持同步/异步/流式执行
- `CloudBrowserPublishTool`: 使用云端浏览器池执行发布

#### 5. 智能路由器 RuntimeRouter ✅

**新增文件：**
- `packages/agent-core/src/agent_core/runtime/router.py` - 智能路由器

**功能说明：**
- 四维路由决策：预算、队列、风控、能力
- 支持本地优先、云端降级策略
- 风险等级评估

### 架构总结

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Agent Runtime 三层架构                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: Agent Definition Layer (Graph 定义层)                             │
│  - YAML/JSON 声明式 Graph 定义                                               │
│  - agent-definitions/*.yaml                                                 │
│                                                                             │
│  Layer 2: Agent Runtime Layer (执行器层)                                    │
│  - LocalExecutor (桌面端/Sidecar)                                           │
│  - CloudExecutor (云端/FastAPI)                                             │
│  - RuntimeRouter (智能路由)                                                  │
│                                                                             │
│  Layer 3: Tool Layer (工具层)                                               │
│  - ToolInterface (统一接口)                                                  │
│  - Local/Cloud 实现                                                         │
│  - ToolRegistry (工具注册表)                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 文件清单

**packages/agent-core/src/agent_core/**
- `__init__.py` - 主模块导出
- `llm/__init__.py` - LLM 模块
- `llm/config.py` - 配置管理
- `llm/cloud_client.py` - 云端客户端
- `llm/direct_client.py` - 直接调用客户端
- `runtime/__init__.py` - 运行时模块
- `runtime/router.py` - 智能路由器
- `graph/__init__.py` - Graph 模块
- `tools/__init__.py` - 工具模块

**apps/sidecar/src/sidecar/**
- `main.py` - JSON-RPC 服务入口
- `tools/browser.py` - 本地浏览器工具
- `tools/credential.py` - 本地凭证工具

**apps/cloud-backend/backend/app/agent/**
- `__init__.py` - Agent 模块
- `executor.py` - 云端执行器
- `tools/__init__.py` - 工具模块
- `tools/browser.py` - 云端浏览器工具

### 后续工作

1. 实现平台适配器（xiaohongshu, douyin, weibo 等）
2. 完善凭证同步功能
3. 实现浏览器池管理
4. 添加单元测试
5. 集成到 Tauri 桌面端

---

*记录时间: 2025-12-28 15:50:00*
*作者: @Ysf*

---

## 2025-12-28 18:00:00 - Agent Runtime 后续工作完成

**时间**: 2025-12-28 18:00:00
**模型**: Claude Opus 4.5 (claude-opus-4-5-20251101)
**任务**: 完成 Agent Runtime 后续工作

### 任务概述

根据计划完成以下 5 项后续工作：
1. 实现平台适配器（抖音、B站）
2. 完善凭证同步功能
3. 实现云端浏览器池管理
4. 添加单元测试
5. 集成到 Tauri 桌面端

### 完成内容

#### Phase 1: 平台适配器 ✅

**新增文件：**
- `packages/agent-core/src/agent_core/platforms/douyin.py` - 抖音适配器
- `packages/agent-core/src/agent_core/platforms/bilibili.py` - B站适配器

**已有文件（确认存在）：**
- `xiaohongshu.py` - 小红书适配器
- `weibo.py` - 微博适配器
- `wechat_mp.py` - 微信公众号适配器

**更新文件：**
- `packages/agent-core/src/agent_core/platforms/__init__.py` - 导出所有适配器

#### Phase 2: 凭证同步服务 ✅

**云端新增文件：**
- `apps/cloud-backend/backend/app/credential/__init__.py`
- `apps/cloud-backend/backend/app/credential/model.py` - SyncedCredential 数据模型
- `apps/cloud-backend/backend/app/credential/schema.py` - Pydantic Schema
- `apps/cloud-backend/backend/app/credential/service.py` - 凭证同步服务
- `apps/cloud-backend/backend/app/credential/api.py` - REST API

**桌面端新增文件：**
- `apps/sidecar/src/sidecar/services/__init__.py`
- `apps/sidecar/src/sidecar/services/credential_sync.py` - 凭证同步客户端

#### Phase 3: 云端浏览器池 ✅

**新增文件：**
- `apps/cloud-backend/backend/app/services/__init__.py`
- `apps/cloud-backend/backend/app/services/browser_pool.py` - BrowserPool 管理器

**功能特性：**
- 实例池化复用
- 平台隔离
- 自动清理空闲实例
- 健康检查

#### Phase 4: 单元测试 ✅

**新增文件：**
- `packages/agent-core/tests/__init__.py`
- `packages/agent-core/tests/conftest.py` - pytest 配置
- `packages/agent-core/tests/test_platforms/__init__.py`
- `packages/agent-core/tests/test_platforms/test_base.py` - 基类测试
- `packages/agent-core/tests/test_platforms/test_xiaohongshu.py` - 小红书测试
- `packages/agent-core/tests/test_runtime/__init__.py`
- `packages/agent-core/tests/test_runtime/test_router.py` - 路由器测试

#### Phase 5: Tauri Sidecar 集成 ✅

**新增文件：**
- `tauri-app/src-tauri/src/sidecar/mod.rs` - SidecarManager
- `tauri-app/src-tauri/src/sidecar/rpc.rs` - JSON-RPC 类型定义
- `tauri-app/src/hooks/useSidecar.ts` - React Hook

**更新文件：**
- `tauri-app/src-tauri/src/lib.rs` - 注册 sidecar 模块和命令
- `tauri-app/src-tauri/src/commands/mod.rs` - 实现 Sidecar 调用

### 文件清单

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `platforms/douyin.py` | 新增 | 抖音适配器 |
| `platforms/bilibili.py` | 新增 | B站适配器 |
| `platforms/__init__.py` | 修改 | 导出新适配器 |
| `credential/model.py` | 新增 | 凭证数据模型 |
| `credential/schema.py` | 新增 | Pydantic Schema |
| `credential/service.py` | 新增 | 凭证服务 |
| `credential/api.py` | 新增 | 凭证 API |
| `services/browser_pool.py` | 新增 | 浏览器池 |
| `services/credential_sync.py` | 新增 | 同步客户端 |
| `tests/test_platforms/*.py` | 新增 | 平台测试 |
| `tests/test_runtime/*.py` | 新增 | 运行时测试 |
| `sidecar/mod.rs` | 新增 | Sidecar 管理 |
| `sidecar/rpc.rs` | 新增 | RPC 类型 |
| `hooks/useSidecar.ts` | 新增 | React Hook |
| `lib.rs` | 修改 | 注册模块 |
| `commands/mod.rs` | 修改 | 实现调用 |

### 架构总结

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     完整 Agent Runtime 架构                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tauri Desktop (tauri-app/)                                                 │
│  ├── src-tauri/src/sidecar/  ← Rust Sidecar 管理                            │
│  └── src/hooks/useSidecar.ts ← React Hook                                   │
│                    ↓ JSON-RPC                                               │
│  Sidecar (apps/sidecar/)                                                    │
│  ├── main.py                 ← JSON-RPC 服务                                │
│  ├── tools/                  ← 本地工具                                     │
│  └── services/credential_sync.py ← 凭证同步                                 │
│                    ↓ HTTP                                                   │
│  Cloud Backend (apps/cloud-backend/)                                        │
│  ├── credential/             ← 凭证同步 API                                 │
│  ├── services/browser_pool.py ← 浏览器池                                    │
│  └── agent/executor.py       ← 云端执行器                                   │
│                                                                             │
│  Agent Core (packages/agent-core/)                                          │
│  ├── platforms/              ← 5个平台适配器                                │
│  ├── llm/                    ← LLM 统一接口                                 │
│  ├── runtime/                ← 执行器 + 路由器                              │
│  └── tests/                  ← 单元测试                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*记录时间: 2025-12-28 18:00:00*
*作者: @Ysf*
