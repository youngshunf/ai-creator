# AI Creator

> 自媒体一体化AI客户端 - 从灵感到变现的全链路AI助手

## 项目简介

AI Creator 是一个面向自媒体创作者的一体化解决方案，通过深度集成AI能力，实现内容创作、管理、发布、运营的全流程自动化。

## 核心特性

- **AI驱动创作**: 集成Claude Agent SDK和LangGraph，实现高质量内容自动生成
- **多平台发布**: 支持小红书、抖音、微信公众号、微博、B站等主流平台
- **智能运营**: 自动采集运营数据，AI分析并给出选题建议
- **端侧重度运行**: 本地运行AI Agent，保护账号隐私

## 技术架构

```
┌─────────────────────────────────────────┐
│           Tauri 2.0 客户端              │
│  ┌─────────────┐  ┌─────────────┐      │
│  │  React UI   │  │  Rust Core  │      │
│  └─────────────┘  └──────┬──────┘      │
│                          │ Sidecar     │
│  ┌───────────────────────┴───────────┐ │
│  │         Python Runtime            │ │
│  │  ┌─────────┐ ┌─────────┐         │ │
│  │  │ Claude  │ │Playwright│         │ │
│  │  │ Agent   │ │ 自动化   │         │ │
│  │  └─────────┘ └─────────┘         │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 目录结构

```
ai-creator/                          # Monorepo 根目录
├── packages/                        # 共享包 (Monorepo 管理)
│   └── agent-core/                  # Python: Agent 核心库
│
├── apps/                            # 应用层 (Monorepo 管理)
│   ├── desktop/                     # Tauri: 桌面端应用
│   ├── sidecar/                     # Python: 桌面端 Sidecar 服务
│   └── landing/                     # 静态: 落地页
│
├── services/                        # 独立服务 (Git Submodule)
│   ├── cloud-backend/               # FastAPI: 云端后端服务
│   ├── cloud-frontend/              # Vue: 云端管理后台
│   ├── mobile-app/                  # UniApp: 移动端应用
│   └── new-api/                     # Go: LLM API 网关
│
├── external/                        # 外部项目 (Git Submodule)
│   ├── BettaFish/                   # 舆情分析系统
│   └── MiroFish/                    # 数据采集系统
│
├── agent-definitions/               # Agent Graph 定义 (YAML)
├── docs/                            # 项目文档
├── .gitmodules                      # Git Submodule 配置
├── pyproject.toml                   # Python workspace 配置
└── pnpm-workspace.yaml              # Node.js workspace 配置
```

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18
- Rust >= 1.70
- uv (Python 包管理器)

### 安装依赖

```bash
# 安装 uv (Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步所有 Python 依赖
uv sync
```

### 开发

```bash
# 克隆项目（包含所有子模块）
git clone --recurse-submodules <repo-url>

# 开发 Sidecar
cd apps/sidecar
uv run python -m sidecar.main

# 开发云端服务
cd services/cloud-backend
uv run uvicorn backend.app.main:app --reload

# 开发桌面端
cd apps/desktop
pnpm install
pnpm run tauri:dev

# 开发移动端
cd services/mobile-app
pnpm install
npm run dev:mp-weixin
```

## 功能模块

| 模块 | 功能描述 | 状态 |
|------|----------|------|
| **创作** | Desktop TipTap editor with an AI writing panel, an image-generator UI, and topic suggestions; agent-core has LLM, image-gen, and content-formatter tools | 🚧 Partial — UI and tools are in the repo; video-script / auto-layout / auto-illustration flows are not clearly complete |
| **管理** | Desktop project management, account management, drafts, and cloud/local sync (stores, APIs, and a sidecar sync scheduler) | 🚧 Partial — project, account, and sync code landed; a full media/idea/knowledge library is not clearly present |
| **发布** | Publish center with queue and scheduling UI; YAML-configured adapters for Xiaohongshu, Douyin, WeChat, Weibo, and Bilibili; sidecar publish executor (Playwright / browser-use) | 🚧 Partial — adapters, scheduler, and UI exist; end-to-end production readiness was not verified here |
| **运营** | Topic recommender in agent-core (NewsNow and TrendRadar providers) plus topic pages in the desktop app | 🚧 Partial — topic suggestion is implemented in code; broader ops analytics / trend tracking is not clearly complete |
| **LLM管理** | Settings UI for credentials, model selection, and usage stats; agent-core LLM client/config | 🚧 Partial — settings screens exist; supplier / model-group / rate-limit admin is not clearly present in this repo |

## 相关文档

- [品牌愿景](./docs/00-品牌愿景.md)
- [系统架构](./docs/01-系统架构.md)
- [桌面端设计](./docs/02-桌面端设计.md)
- [移动端设计](./docs/03-移动端设计.md)
- [云端服务设计](./docs/04-云端服务设计.md)
- [Agent Runtime](./docs/05-Agent-Runtime.md)
- [BettaFish舆情分析集成](./docs/08-BettaFish舆情分析集成.md)
- [开发规范](./docs/11-开发规范.md)

## 开发团队

@author Ysf

## License

MIT
