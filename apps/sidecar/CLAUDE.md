# Sidecar - AI 上下文文档

> **路径**: `apps/sidecar/`
> **类型**: Python Sidecar 服务
> **作者**: @Ysf

---

## 📋 模块概览

**Sidecar** 是桌面端的 Python 后台服务，通过 JSON-RPC 与 Tauri 进行通信。

### 核心定位

- 提供本地 Agent 执行能力
- 管理本地浏览器自动化
- 安全存储本地凭证
- 定时任务调度

### 依赖关系

```
agent-core
    ↑
sidecar (依赖 agent-core)
    ↑
Tauri Desktop (通过 JSON-RPC 调用)
```

---

## 🏗️ 目录结构

```
apps/sidecar/
├── pyproject.toml                       # 包配置
├── README.md                            # 包说明
├── CLAUDE.md                            # 本文档
│
└── src/sidecar/                         # 源代码
    ├── __init__.py                      # 模块导出
    ├── main.py                          # JSON-RPC 服务入口
    ├── executor.py                      # LocalExecutor
    │
    ├── tools/                           # 本地工具
    │   ├── __init__.py
    │   ├── browser.py                   # 浏览器工具
    │   └── credential.py                # 凭证工具
    │
    ├── services/                        # 本地服务
    │   ├── __init__.py
    │   └── credential_sync.py           # 凭证同步客户端
    │
    ├── browser/                         # 浏览器管理
    │   ├── __init__.py
    │   ├── manager.py                   # 浏览器管理器
    │   └── fingerprint.py               # 指纹管理
    │
    └── scheduler/                       # 定时任务
        ├── __init__.py
        └── publish_scheduler.py         # 发布调度器
```

---

## 🔧 核心功能

### 1. JSON-RPC 服务

**文件**: `src/sidecar/main.py`

**功能**:
- 通过 stdin/stdout 与 Tauri 通信
- 实现 JSON-RPC 2.0 协议
- 支持同步和流式执行

**支持的方法**:
- `initialize` - 初始化服务
- `execute_graph` - 同步执行 Graph
- `execute_graph_stream` - 流式执行 Graph
- `list_graphs` - 列出可用 Graph
- `health_check` - 健康检查
- `login` - 用户登录
- `logout` - 用户登出
- `get_models` - 获取模型列表
- `shutdown` - 关闭服务

### 2. LocalExecutor

**文件**: `src/sidecar/executor.py`

**功能**:
- 加载 Graph 定义
- 执行 Graph 节点
- 调用本地工具
- 事件流推送

### 3. 本地浏览器工具

**文件**: `src/sidecar/tools/browser.py`

**功能**:
- `LocalBrowserPublishTool` - 本地浏览器发布
- `LocalBrowserScrapeTool` - 本地数据采集

**特性**:
- Playwright 浏览器自动化
- 指纹管理
- Cookie 管理
- 截图与日志

### 4. 本地凭证工具

**文件**: `src/sidecar/tools/credential.py`

**功能**:
- `LocalCredentialTool` - 凭证管理

**特性**:
- AES-256-GCM 加密
- 本地安全存储
- 凭证同步（可选）

---

## 📦 依赖管理

### pyproject.toml

```toml
[project]
name = "sidecar"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "agent-core",
    "playwright>=1.40.0",
    "apscheduler>=3.10.0",
    "cryptography>=41.0.0",
]
```

---

## 🔗 JSON-RPC 协议

### 请求格式

```json
{
  "jsonrpc": "2.0",
  "method": "execute_graph",
  "params": {
    "graph_name": "content-creation",
    "inputs": {
      "topic": "AI 创作工具",
      "platform": "xiaohongshu"
    }
  },
  "id": 1
}
```

### 响应格式

```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "outputs": {
      "content": "...",
      "images": ["asset://local/image/abc123"]
    },
    "execution_id": "run-xxx",
    "trace_id": "tr-xxx",
    "execution_time": 12.5
  },
  "id": 1
}
```

### 事件流 (流式执行)

```json
{
  "jsonrpc": "2.0",
  "method": "event",
  "params": {
    "type": "node_started",
    "data": {
      "node_name": "generate_outline",
      "timestamp": "2025-12-28T21:00:00Z"
    }
  }
}
```

---

## 🧪 开发

### 启动服务

```bash
# 开发模式
uv run python -m sidecar.main

# 生产模式
uv run --frozen python -m sidecar.main
```

### 测试

```bash
# 运行测试
uv run pytest

# 测试 JSON-RPC 通信
echo '{"jsonrpc":"2.0","method":"health_check","params":{},"id":1}' | uv run python -m sidecar.main
```

---

## 🔗 关键文件

| 文件 | 说明 | 优先级 |
|------|------|--------|
| `main.py` | JSON-RPC 服务入口 | P0 |
| `executor.py` | LocalExecutor | P0 |
| `tools/browser.py` | 浏览器工具 | P0 |
| `tools/credential.py` | 凭证工具 | P0 |
| `services/credential_sync.py` | 凭证同步 | P1 |
| `browser/manager.py` | 浏览器管理器 | P1 |
| `scheduler/publish_scheduler.py` | 发布调度器 | P1 |

---

## 📚 相关文档

- [桌面端设计](../../docs/02-桌面端设计.md)
- [Agent Runtime](../../docs/05-Agent-Runtime.md)
- [开发规范](../../docs/11-开发规范.md)

---

## 🔼 导航

[← 返回根目录](../../CLAUDE.md)
