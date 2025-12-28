# Desktop App - AI 上下文文档

> **路径**: `apps/desktop/`
> **类型**: Tauri 2.0 桌面应用
> **作者**: @Ysf

---

## 📋 模块概览

**Desktop App** 是 AI Creator 的桌面端应用，基于 Tauri 2.0 构建。

### 核心定位

- 完整功能 + 本地能力
- Python Sidecar 支持本地 Agent 执行
- Playwright 本地浏览器自动化
- 本地凭证加密存储
- 离线能力完整

### 技术栈

- **前端**: React 19 + TanStack Router + TanStack Query + Zustand
- **后端**: Rust + Tauri 2.0
- **编辑器**: TipTap (富文本编辑器)
- **UI**: Tailwind CSS + shadcn/ui
- **表单**: React Hook Form + Zod

---

## 🏗️ 目录结构

```
apps/desktop/
├── package.json                         # Node.js 配置
├── tsconfig.json                        # TypeScript 配置
├── vite.config.ts                       # Vite 配置
├── tailwind.config.js                   # Tailwind 配置
├── README.md                            # 项目说明
├── CLAUDE.md                            # 本文档
│
├── src/                                 # React 前端
│   ├── main.tsx                         # 应用入口
│   ├── index.css                        # 全局样式
│   │
│   ├── routes/                          # 路由页面
│   │   ├── __root.tsx                   # 根路由
│   │   ├── index.tsx                    # 首页
│   │   ├── creation/                    # 创作模块
│   │   │   └── index.tsx                # 创作工作台
│   │   ├── publish/                     # 发布模块
│   │   │   └── index.tsx                # 发布中心
│   │   └── settings/                    # 设置模块
│   │       └── index.tsx                # 设置中心
│   │
│   ├── components/                      # UI 组件
│   │   ├── layout/                      # 布局组件
│   │   │   ├── MainLayout.tsx           # 主布局
│   │   │   ├── Header.tsx               # 顶部导航
│   │   │   └── Sidebar.tsx              # 侧边栏
│   │   │
│   │   ├── editor/                      # 编辑器组件
│   │   │   ├── TipTapEditor.tsx         # TipTap 编辑器
│   │   │   ├── EditorToolbar.tsx        # 编辑器工具栏
│   │   │   ├── AIAssistMenu.tsx         # AI 辅助菜单
│   │   │   ├── AIWritingPanel.tsx       # AI 写作面板
│   │   │   └── StyleSelector.tsx        # 风格选择器
│   │   │
│   │   ├── publish/                     # 发布组件
│   │   │   ├── PublishCenter.tsx        # 发布中心
│   │   │   ├── PlatformCard.tsx         # 平台卡片
│   │   │   ├── ContentAdapter.tsx       # 内容适配器
│   │   │   ├── PreviewPanel.tsx         # 预览面板
│   │   │   └── ScheduleForm.tsx         # 定时发布表单
│   │   │
│   │   ├── settings/                    # 设置组件
│   │   │   ├── ModelSelector.tsx        # 模型选择器
│   │   │   └── UsageStats.tsx           # 用量统计
│   │   │
│   │   └── common/                      # 通用组件
│   │       └── ConnectionStatus.tsx     # 连接状态
│   │
│   ├── hooks/                           # React Hooks
│   │   ├── useSidecar.ts                # Sidecar 通信
│   │   ├── useAgent.ts                  # Agent 执行
│   │   └── useLLM.ts                    # LLM 调用
│   │
│   ├── stores/                          # Zustand 状态管理
│   │   ├── authStore.ts                 # 认证状态
│   │   ├── editorStore.ts               # 编辑器状态
│   │   └── publishStore.ts              # 发布状态
│   │
│   ├── lib/                             # 工具库
│   │   ├── api.ts                       # API 客户端
│   │   └── utils.ts                     # 工具函数
│   │
│   └── types/                           # TypeScript 类型
│       ├── sidecar.ts                   # Sidecar 类型
│       └── agent.ts                     # Agent 类型
│
└── src-tauri/                           # Rust 后端
    ├── Cargo.toml                       # Rust 配置
    ├── tauri.conf.json                  # Tauri 配置
    ├── build.rs                         # 构建脚本
    │
    └── src/                             # Rust 源代码
        ├── main.rs                      # 主入口
        ├── lib.rs                       # 库入口
        │
        ├── sidecar/                     # Sidecar 管理
        │   ├── mod.rs                   # Sidecar 管理器
        │   └── rpc.rs                   # JSON-RPC 类型
        │
        └── commands/                    # Tauri 命令
            └── mod.rs                   # 命令实现
```

---

## 🔧 核心功能

### 1. 创作工作台

**路由**: `/creation`

**功能**:
- TipTap 富文本编辑器
- AI 辅助写作 (续写、改写、扩写)
- 风格选择 (正式、轻松、专业等)
- 实时字数统计
- 自动保存草稿

**关键组件**:
- `TipTapEditor.tsx` - 编辑器主体
- `AIAssistMenu.tsx` - AI 辅助菜单
- `AIWritingPanel.tsx` - AI 写作面板

### 2. 发布中心

**路由**: `/publish`

**功能**:
- 多平台一键发布
- 内容适配 (自动调整格式)
- 定时发布
- 发布历史
- 发布状态追踪

**关键组件**:
- `PublishCenter.tsx` - 发布中心主体
- `PlatformCard.tsx` - 平台卡片
- `ContentAdapter.tsx` - 内容适配器
- `ScheduleForm.tsx` - 定时发布表单

### 3. 设置中心

**路由**: `/settings`

**功能**:
- LLM 模型选择
- 用量统计
- 凭证管理
- 同步设置

**关键组件**:
- `ModelSelector.tsx` - 模型选择器
- `UsageStats.tsx` - 用量统计

---

## 🔗 Sidecar 通信

### useSidecar Hook

**文件**: `src/hooks/useSidecar.ts`

```typescript
export function useSidecar() {
  const executeGraph = async (
    graphName: string,
    inputs: Record<string, any>
  ) => {
    const result = await invoke('sidecar_execute_graph', {
      graphName,
      inputs,
    });
    return result;
  };

  const executeGraphStream = async (
    graphName: string,
    inputs: Record<string, any>,
    onEvent: (event: AgentEvent) => void
  ) => {
    // 流式执行
  };

  return {
    executeGraph,
    executeGraphStream,
  };
}
```

### Rust 命令

**文件**: `src-tauri/src/commands/mod.rs`

```rust
#[tauri::command]
pub async fn sidecar_execute_graph(
    graph_name: String,
    inputs: serde_json::Value,
    state: tauri::State<'_, SidecarManager>,
) -> Result<serde_json::Value, String> {
    state.execute_graph(graph_name, inputs).await
}
```

---

## 📦 依赖管理

### package.json

```json
{
  "name": "creatorflow-desktop",
  "version": "0.1.0",
  "dependencies": {
    "@tanstack/react-query": "^5.62.8",
    "@tanstack/react-router": "^1.93.0",
    "@tauri-apps/api": "^2.1.1",
    "@tiptap/react": "^3.14.0",
    "react": "^19.0.0",
    "react-hook-form": "^7.54.2",
    "zod": "^3.24.1",
    "zustand": "^5.0.9"
  }
}
```

---

## 🧪 开发

### 启动开发服务器

```bash
# 启动 Tauri 开发模式
pnpm run tauri:dev

# 仅启动前端
pnpm run dev

# 构建生产版本
pnpm run tauri:build
```

---

## 🔗 关键文件

| 文件 | 说明 | 优先级 |
|------|------|--------|
| `src/main.tsx` | 应用入口 | P0 |
| `src/hooks/useSidecar.ts` | Sidecar 通信 | P0 |
| `src/components/editor/TipTapEditor.tsx` | 编辑器 | P0 |
| `src/components/publish/PublishCenter.tsx` | 发布中心 | P0 |
| `src-tauri/src/lib.rs` | Rust 主入口 | P0 |
| `src-tauri/src/sidecar/mod.rs` | Sidecar 管理器 | P0 |

---

## 📚 相关文档

- [桌面端设计](../../docs/02-桌面端设计.md)
- [桌面端开发计划](../../docs/15-桌面端开发计划.md)
- [开发规范](../../docs/11-开发规范.md)

---

## 🔼 导航

[← 返回根目录](../../CLAUDE.md)
