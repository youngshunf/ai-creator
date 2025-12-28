# AI Creator - Agent Runtime

> 端云统一 Agent Runtime 抽象层（三层架构设计）

## 1. 设计理念

### 1.1 核心目标

**Graph/Agent 代码"唯一来源"，端云统一执行**

- **单一来源**: Graph 定义文件版本控制，端侧和云端共享同一份代码
- **端云对等**: 相同的 Graph 在本地或云端执行，行为一致
- **工具隔离**: 工具层屏蔽平台差异，通过能力声明和降级路径处理
- **资源统一**: 统一资源 URI 方案，避免硬编码路径

### 1.2 三层架构概览

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Agent Runtime 三层架构                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Layer 1: Agent Definition Layer                          │  │
│  │                     (Graph 定义层)                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  YAML/JSON 声明式 Graph 定义 (唯一来源，版本控制)                  │  │  │
│  │  │                                                                 │  │  │
│  │  │  ├── agent-definitions/                                         │  │  │
│  │  │  │   ├── content-creation.yaml    # 内容创作 Graph              │  │  │
│  │  │  │   ├── publish-workflow.yaml    # 发布工作流 Graph            │  │  │
│  │  │  │   ├── analytics.yaml           # 数据分析 Graph              │  │  │
│  │  │  │   └── topic-recommend.yaml     # 选题推荐 Graph              │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      │ GraphLoader.load()                   │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Layer 2: Agent Runtime Layer                             │  │
│  │                    (执行器层)                                          │  │
│  │                                                                       │  │
│  │       ┌─────────────────┐              ┌─────────────────┐           │  │
│  │       │  LocalExecutor  │              │  CloudExecutor  │           │  │
│  │       │  (桌面端/Python) │              │  (云端/FastAPI) │           │  │
│  │       └────────┬────────┘              └────────┬────────┘           │  │
│  │                │                                │                    │  │
│  │                └────────────┬───────────────────┘                    │  │
│  │                             │                                        │  │
│  │                             │ ToolRegistry.get(tool_name)            │  │
│  │                             ▼                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              Layer 3: Tool Layer                                      │  │
│  │                   (工具层)                                             │  │
│  │                                                                       │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │  │
│  │  │ ToolInterface  │  │ ToolInterface  │  │ ToolInterface  │          │  │
│  │  │ (统一接口)      │  │ (统一接口)      │  │ (统一接口)      │          │  │
│  │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘          │  │
│  │          │                   │                   │                   │  │
│  │   ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐            │  │
│  │   │ Local Impl  │     │ Cloud Impl  │     │ Mock Impl   │            │  │
│  │   │ (本地实现)   │     │ (云端实现)   │     │ (测试实现)   │            │  │
│  │   └─────────────┘     └─────────────┘     └─────────────┘            │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 端云代码共享策略

### 2.1 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **Monorepo + uv Workspace** ✅ | 版本同步自动、开发体验好、部署灵活 | 仓库较大 | **推荐方案** |
| 独立仓库 + PyPI | 解耦清晰 | 版本同步困难、发布流程复杂 | 开源共享 |
| Git Submodule | 代码隔离 | 管理复杂、开发体验差 | 多团队协作 |
| 复制代码 | 简单 | 维护噩梦 | ❌ 不推荐 |

### 2.2 推荐架构：Monorepo + uv Workspace

```text
ai-creator/                              # Monorepo 根目录
├── pyproject.toml                       # Workspace 定义
├── uv.lock                              # 锁定依赖版本
│
├── packages/                            # 🔥 共享包目录
│   └── agent-core/                      # 核心共享包
│       ├── pyproject.toml               # 包定义
│       └── src/
│           └── agent_core/              # Python 包
│               ├── __init__.py
│               ├── graph/               # Graph 加载/编译
│               ├── runtime/             # 运行时接口
│               ├── tools/               # 工具层基类
│               ├── resource/            # 资源管理
│               └── crypto/              # 加密工具
│
├── apps/                                # 🔥 应用目录
│   ├── sidecar/                         # 桌面端 Python Sidecar
│   │   ├── pyproject.toml               # 依赖 agent-core
│   │   └── src/
│   │       └── sidecar/
│   │           ├── executor.py          # LocalExecutor
│   │           ├── tools/               # 本地工具实现
│   │           └── main.py
│   │
│   └── cloud-backend/                   # 云端服务
│       ├── pyproject.toml               # 依赖 agent-core
│       └── backend/
│           └── app/
│               └── agent/
│                   ├── executor.py      # CloudExecutor
│                   └── tools/           # 云端工具实现
│
├── agent-definitions/                   # Graph 定义（共享）
│   ├── content-creation.yaml
│   └── publish-workflow.yaml
│
└── apps/desktop/                        # Tauri 桌面应用
    └── src-tauri/
        └── sidecar/                     # Sidecar 二进制
```

### 2.3 Workspace 配置

```toml
# ai-creator/pyproject.toml (Monorepo 根)

[project]
name = "ai-creator-workspace"
version = "0.1.0"
requires-python = ">=3.11"

[tool.uv]
# 定义 workspace 成员
workspace = { members = ["packages/*", "apps/*"] }

[tool.uv.sources]
# 本地包源定义（所有 workspace 成员自动可用）
agent-core = { workspace = true }
```

```toml
# packages/agent-core/pyproject.toml

[project]
name = "agent-core"
version = "0.1.0"
description = "AI Creator Agent Core - 端云共享核心"
requires-python = ">=3.11"

dependencies = [
    "langgraph>=0.2.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
    "anthropic>=0.40.0",
    "cryptography>=42.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/agent_core"]
```

```toml
# apps/sidecar/pyproject.toml

[project]
name = "ai-creator-sidecar"
version = "0.1.0"
description = "AI Creator 桌面端 Python Sidecar"
requires-python = ">=3.11"

dependencies = [
    "agent-core",           # 🔥 workspace 引用，无需版本号
    "playwright>=1.40.0",
    "uvicorn>=0.30.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```toml
# services/cloud-backend/pyproject.toml

[project]
name = "ai-creator-cloud"
version = "0.1.0"
description = "AI Creator 云端服务"
requires-python = ">=3.11"

dependencies = [
    "agent-core",           # 🔥 workspace 引用
    "fastapi>=0.115.0",
    "celery>=5.4.0",
    "redis>=5.0.0",
    "sqlalchemy>=2.0.0",
]
```

### 2.4 开发工作流

```bash
# 1. 初始化 workspace
cd ai-creator
uv sync                                 # 安装所有依赖

# 2. 开发 agent-core（修改共享代码）
cd packages/agent-core
# 修改代码...
uv run pytest                           # 测试

# 3. 开发 sidecar（自动使用最新 agent-core）
cd apps/sidecar
uv run python -m sidecar.main           # 运行

# 4. 开发云端（自动使用最新 agent-core）
cd services/cloud-backend
uv run uvicorn backend.app.main:app     # 运行

# 5. 构建 sidecar 发布包
cd apps/sidecar
uv build                                # 生成 wheel/tar.gz
# 或使用 PyInstaller 打包二进制
pyinstaller --onefile src/sidecar/main.py
```

---

## 3. 核心代码设计

### 3.1 agent-core 包结构

```text
packages/agent-core/src/agent_core/
├── __init__.py
│
├── graph/                               # Layer 1: Graph 定义层
│   ├── __init__.py
│   ├── loader.py                        # GraphLoader: 加载 YAML/JSON
│   ├── compiler.py                      # GraphCompiler: 编译为 LangGraph
│   ├── validator.py                     # 验证 Graph 定义
│   └── types.py                         # Graph 类型定义
│
├── runtime/                             # Layer 2: 运行时层
│   ├── __init__.py
│   ├── interfaces.py                    # ExecutorInterface 抽象基类
│   ├── context.py                       # RuntimeContext 运行时上下文
│   ├── events.py                        # AgentEvent 事件定义
│   └── router.py                        # RuntimeRouter 智能路由
│
├── tools/                               # Layer 3: 工具层
│   ├── __init__.py
│   ├── base.py                          # ToolInterface 抽象基类
│   ├── registry.py                      # ToolRegistry 工具注册表
│   ├── capability.py                    # 能力声明
│   │
│   ├── builtin/                         # 内置工具（端云共用）
│   │   ├── __init__.py
│   │   ├── llm.py                       # LLM 工具
│   │   ├── web_search.py                # 网络搜索
│   │   └── storage.py                   # 存储工具
│   │
│   └── stubs/                           # 工具桩（需要端/云实现）
│       ├── __init__.py
│       ├── browser.py                   # 浏览器工具接口
│       └── credential.py                # 凭证工具接口
│
├── resource/                            # 资源管理
│   ├── __init__.py
│   ├── uri.py                           # AssetURI 统一资源标识
│   └── resolver.py                      # AssetResolver 抽象基类
│
├── crypto/                              # 加密工具
│   ├── __init__.py
│   └── credential_crypto.py             # 凭证加密
│
└── platforms/                           # 平台适配器
    ├── __init__.py
    ├── base.py                          # PlatformAdapter 基类
    ├── xiaohongshu.py
    ├── douyin.py
    └── ...
```

### 3.2 运行时接口设计

```python
# packages/agent-core/src/agent_core/runtime/interfaces.py

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

class RuntimeType(Enum):
    """运行时类型"""
    LOCAL = "local"       # 本地 Python Sidecar
    CLOUD = "cloud"       # 云端服务


@dataclass
class RuntimeContext:
    """运行时上下文 - 统一端云配置注入"""
    runtime_type: RuntimeType
    user_id: str
    inputs: dict

    # 模型配置
    model_default: str = "claude-sonnet-4-20250514"
    model_fast: str = "claude-3-5-haiku-20241022"

    # API 密钥（运行时注入，不硬编码）
    api_keys: dict = field(default_factory=dict)

    # 资源解析器（由端/云实现注入）
    asset_resolver: Optional["AssetResolver"] = None

    # 额外上下文（端/云特有）
    extra: dict = field(default_factory=dict)


@dataclass
class ExecutionRequest:
    """执行请求"""
    graph_name: str                    # Graph 名称
    inputs: dict                       # 输入参数
    user_id: str                       # 用户ID
    session_id: Optional[str] = None   # 会话ID（断点续传）
    timeout: int = 300                 # 超时时间(秒)
    trace_id: Optional[str] = None     # 追踪ID


@dataclass
class ExecutionResponse:
    """执行响应"""
    success: bool
    outputs: Any
    error: Optional[str] = None
    execution_id: str = ""
    execution_time: float = 0.0
    runtime_type: RuntimeType = RuntimeType.LOCAL
    trace_id: str = ""


@dataclass
class AgentEvent:
    """Agent 执行事件"""
    event_type: str          # node_started | tool_called | completed | failed
    run_id: str
    trace_id: str
    timestamp: datetime
    data: dict

    # Token 使用追踪
    tokens_used: int = 0
    cost_cents: int = 0


class ExecutorInterface(ABC):
    """执行器接口 - 端云统一"""

    runtime_type: RuntimeType

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """同步执行 Graph"""
        pass

    @abstractmethod
    async def execute_stream(
        self, request: ExecutionRequest
    ) -> AsyncIterator[AgentEvent]:
        """流式执行 Graph，返回事件流"""
        pass

    @abstractmethod
    async def get_status(self, execution_id: str) -> dict:
        """获取执行状态"""
        pass

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """取消执行"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

### 3.3 工具层设计

```python
# packages/agent-core/src/agent_core/tools/base.py

from abc import ABC, abstractmethod
from typing import Any, Optional, ClassVar
from dataclasses import dataclass, field
from enum import Enum

from ..runtime.interfaces import RuntimeType


class ToolCapability(Enum):
    """工具能力标识"""
    LLM_GENERATE = "llm_generate"
    WEB_SEARCH = "web_search"
    IMAGE_GEN = "image_gen"
    BROWSER_AUTOMATION = "browser_automation"
    FILE_STORAGE = "file_storage"
    CREDENTIAL_STORE = "credential_store"
    HOT_TOPIC_DISCOVERY = "hot_topic_discovery"      # BettaFish 热点发现
    SENTIMENT_ANALYSIS = "sentiment_analysis"         # BettaFish 情感分析


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    capabilities: list[ToolCapability]
    supported_runtimes: list[RuntimeType] = field(
        default_factory=lambda: [RuntimeType.LOCAL, RuntimeType.CLOUD]
    )
    fallback_tool: Optional[str] = None
    requires_auth: bool = False


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error: Optional[str] = None


class ToolInterface(ABC):
    """工具基类 - 统一接口"""

    metadata: ClassVar[ToolMetadata]

    @abstractmethod
    async def execute(self, ctx: "RuntimeContext", **kwargs) -> ToolResult:
        """执行工具 - 接收运行时上下文"""
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """获取输入参数 JSON Schema"""
        pass

    def is_available(self, ctx: "RuntimeContext") -> bool:
        """检查工具在当前运行时是否可用"""
        return ctx.runtime_type in self.metadata.supported_runtimes
```

```python
# packages/agent-core/src/agent_core/tools/registry.py

from typing import Type, Optional, Dict
from .base import ToolInterface, ToolCapability
from ..runtime.interfaces import RuntimeType, RuntimeContext


class ToolRegistry:
    """
    工具注册表 - 端云统一管理

    使用方式:
        # 注册工具（在端/云启动时）
        ToolRegistry.register("browser_publish", RuntimeType.LOCAL)(LocalBrowserTool)
        ToolRegistry.register("browser_publish", RuntimeType.CLOUD)(CloudBrowserTool)

        # 获取工具（在执行时）
        registry = ToolRegistry(runtime_type=RuntimeType.LOCAL)
        tool = registry.get("browser_publish")
    """

    # 全局注册表: {tool_name: {runtime_type: tool_class}}
    _tools: Dict[str, Dict[RuntimeType, Type[ToolInterface]]] = {}

    @classmethod
    def register(cls, name: str, runtime_type: RuntimeType):
        """装饰器：注册工具到指定运行时"""
        def decorator(tool_class: Type[ToolInterface]):
            if name not in cls._tools:
                cls._tools[name] = {}
            cls._tools[name][runtime_type] = tool_class
            return tool_class
        return decorator

    @classmethod
    def register_universal(cls, name: str):
        """装饰器：注册工具到所有运行时（端云共用）"""
        def decorator(tool_class: Type[ToolInterface]):
            if name not in cls._tools:
                cls._tools[name] = {}
            cls._tools[name][RuntimeType.LOCAL] = tool_class
            cls._tools[name][RuntimeType.CLOUD] = tool_class
            return tool_class
        return decorator

    def __init__(self, runtime_type: RuntimeType):
        self.runtime_type = runtime_type
        self._instances: Dict[str, ToolInterface] = {}

    def get(
        self,
        name: str,
        ctx: Optional[RuntimeContext] = None
    ) -> Optional[ToolInterface]:
        """获取工具实例"""
        rt = ctx.runtime_type if ctx else self.runtime_type

        cache_key = f"{name}:{rt.value}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        if name not in self._tools:
            return None

        tool_class = self._tools[name].get(rt)
        if tool_class is None:
            return None

        instance = tool_class()
        self._instances[cache_key] = instance
        return instance

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self._tools.keys())

    def list_available_tools(self, ctx: RuntimeContext) -> list[str]:
        """列出当前运行时可用的工具"""
        available = []
        for name in self._tools:
            tool = self.get(name, ctx)
            if tool and tool.is_available(ctx):
                available.append(name)
        return available
```

### 3.4 内置工具示例（端云共用）

```python
# packages/agent-core/src/agent_core/tools/builtin/llm.py

from ..base import ToolInterface, ToolMetadata, ToolCapability, ToolResult
from ..registry import ToolRegistry
from ...runtime.interfaces import RuntimeContext


@ToolRegistry.register_universal("llm_generate")
class LLMGenerateTool(ToolInterface):
    """LLM 文本生成工具 - 端云共用实现"""

    metadata = ToolMetadata(
        name="llm_generate",
        description="使用 LLM 生成文本",
        capabilities=[ToolCapability.LLM_GENERATE],
    )

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ToolResult:
        """执行 LLM 生成"""
        from anthropic import Anthropic

        # 从运行时上下文获取 API Key
        api_key = ctx.api_keys.get("anthropic")
        if not api_key:
            return ToolResult(success=False, data=None, error="Missing Anthropic API key")

        # 使用配置的模型或默认模型
        model = model or ctx.model_default

        try:
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

            return ToolResult(
                success=True,
                data={
                    "content": response.content[0].text,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "用户提示"},
                "system": {"type": "string", "description": "系统提示"},
                "model": {"type": "string", "description": "模型名称"},
                "max_tokens": {"type": "integer", "default": 4096},
                "temperature": {"type": "number", "default": 0.7},
            },
            "required": ["prompt"]
        }
```

### 3.5 端侧专用工具（Sidecar 实现）

```python
# apps/sidecar/src/sidecar/tools/browser.py

from agent_core.tools.base import ToolInterface, ToolMetadata, ToolCapability, ToolResult
from agent_core.tools.registry import ToolRegistry
from agent_core.runtime.interfaces import RuntimeType, RuntimeContext


@ToolRegistry.register("browser_publish", RuntimeType.LOCAL)
class LocalBrowserPublishTool(ToolInterface):
    """本地浏览器发布工具 - 仅端侧可用"""

    metadata = ToolMetadata(
        name="browser_publish",
        description="使用本地 Playwright 浏览器发布内容",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        platform: str,
        account_id: str,
        content: dict,
    ) -> ToolResult:
        """使用本地 Playwright 发布"""
        from agent_core.platforms import get_adapter
        from playwright.async_api import async_playwright

        try:
            # 从上下文获取浏览器管理器
            browser_manager = ctx.extra.get("browser_manager")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()

                # 加载本地保存的凭证
                await self._load_credentials(context, platform, account_id)

                page = await context.new_page()
                adapter = get_adapter(platform)
                result = await adapter.publish(page, content)

                await browser.close()
                return ToolResult(success=True, data=result)

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _load_credentials(self, context, platform: str, account_id: str):
        """加载本地加密的凭证"""
        # 从本地存储解密并加载凭证
        pass

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["xiaohongshu", "douyin", "weibo"]},
                "account_id": {"type": "string"},
                "content": {"type": "object"},
            },
            "required": ["platform", "account_id", "content"]
        }
```

### 3.6 云端专用工具（Backend 实现）

```python
# services/cloud-backend/backend/app/agent/tools/browser.py

from agent_core.tools.base import ToolInterface, ToolMetadata, ToolCapability, ToolResult
from agent_core.tools.registry import ToolRegistry
from agent_core.runtime.interfaces import RuntimeType, RuntimeContext


@ToolRegistry.register("browser_publish", RuntimeType.CLOUD)
class CloudBrowserPublishTool(ToolInterface):
    """云端浏览器发布工具 - 使用浏览器池"""

    metadata = ToolMetadata(
        name="browser_publish",
        description="使用云端浏览器池发布内容",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.CLOUD],
    )

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        platform: str,
        account_id: str,
        content: dict,
    ) -> ToolResult:
        """使用云端浏览器池发布"""
        from backend.app.browser.pool import BrowserPool

        try:
            # 从上下文获取浏览器池
            browser_pool: BrowserPool = ctx.extra.get("browser_pool")

            # 获取用户同步的凭证（需要用户开启凭证同步）
            credential = await self._get_synced_credential(
                ctx.user_id, platform, account_id
            )
            if not credential:
                return ToolResult(
                    success=False,
                    data=None,
                    error="未找到同步的凭证，请在桌面端开启凭证同步"
                )

            # 从浏览器池获取实例
            browser_context = await browser_pool.acquire(platform, credential)

            try:
                result = await browser_context.publish(content)
                return ToolResult(success=True, data=result)
            finally:
                await browser_pool.release(browser_context)

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def _get_synced_credential(self, user_id: str, platform: str, account_id: str):
        """获取用户同步的凭证"""
        # 从数据库查询加密的凭证
        pass

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "account_id": {"type": "string"},
                "content": {"type": "object"},
            },
            "required": ["platform", "account_id", "content"]
        }
```

---

## 4. 本地执行器实现

```python
# apps/sidecar/src/sidecar/executor.py

import time
import uuid
from typing import AsyncIterator

from agent_core.runtime.interfaces import (
    ExecutorInterface, RuntimeType, RuntimeContext,
    ExecutionRequest, ExecutionResponse, AgentEvent
)
from agent_core.graph.loader import GraphLoader
from agent_core.graph.compiler import GraphCompiler
from agent_core.tools.registry import ToolRegistry
from agent_core.resource.resolver import LocalAssetResolver


class LocalExecutor(ExecutorInterface):
    """本地执行器 - 桌面端 Python Sidecar"""

    runtime_type = RuntimeType.LOCAL

    def __init__(self, config: dict):
        self.config = config
        self.graph_loader = GraphLoader(
            definitions_path=config.get('definitions_path', 'agent-definitions')
        )
        self.tool_registry = ToolRegistry(RuntimeType.LOCAL)
        self.compiler = GraphCompiler(self.tool_registry)
        self._executions: dict[str, dict] = {}

    def _create_context(self, request: ExecutionRequest) -> RuntimeContext:
        """创建运行时上下文"""
        return RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id=request.user_id,
            inputs=request.inputs,
            model_default=self.config.get('default_model', 'claude-sonnet-4-20250514'),
            model_fast=self.config.get('fast_model', 'claude-3-5-haiku-20241022'),
            api_keys={
                "anthropic": self.config.get('anthropic_api_key'),
            },
            asset_resolver=LocalAssetResolver(self.config),
            extra={
                "browser_manager": self._get_browser_manager(),
            }
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """执行 Graph"""
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or f"tr-{uuid.uuid4()}"
        start_time = time.time()

        try:
            # 加载 Graph 定义
            definition = self.graph_loader.load(request.graph_name)

            # 创建运行时上下文
            ctx = self._create_context(request)

            # 编译并执行
            graph = self.compiler.compile(definition, ctx)
            initial_state = self._create_initial_state(definition['spec']['state'])
            final_state = await graph.ainvoke(initial_state)

            # 提取输出
            outputs = self._extract_outputs(definition['spec']['outputs'], final_state)

            return ExecutionResponse(
                success=True,
                outputs=outputs,
                execution_id=execution_id,
                execution_time=time.time() - start_time,
                runtime_type=self.runtime_type,
                trace_id=trace_id,
            )

        except Exception as e:
            return ExecutionResponse(
                success=False,
                outputs=None,
                error=str(e),
                execution_id=execution_id,
                execution_time=time.time() - start_time,
                runtime_type=self.runtime_type,
                trace_id=trace_id,
            )

    async def execute_stream(
        self, request: ExecutionRequest
    ) -> AsyncIterator[AgentEvent]:
        """流式执行，返回事件流"""
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or f"tr-{uuid.uuid4()}"

        # 发送开始事件
        yield AgentEvent(
            event_type="run_started",
            run_id=execution_id,
            trace_id=trace_id,
            timestamp=datetime.now(),
            data={"graph_name": request.graph_name}
        )

        try:
            definition = self.graph_loader.load(request.graph_name)
            ctx = self._create_context(request)
            graph = self.compiler.compile(definition, ctx)

            # 使用 astream_events 获取详细事件
            initial_state = self._create_initial_state(definition['spec']['state'])

            async for event in graph.astream_events(initial_state):
                yield AgentEvent(
                    event_type=event["event"],
                    run_id=execution_id,
                    trace_id=trace_id,
                    timestamp=datetime.now(),
                    data=event.get("data", {}),
                )

            yield AgentEvent(
                event_type="run_completed",
                run_id=execution_id,
                trace_id=trace_id,
                timestamp=datetime.now(),
                data={}
            )

        except Exception as e:
            yield AgentEvent(
                event_type="run_failed",
                run_id=execution_id,
                trace_id=trace_id,
                timestamp=datetime.now(),
                data={"error": str(e)}
            )

    async def get_status(self, execution_id: str) -> dict:
        return self._executions.get(execution_id, {"status": "not_found"})

    async def cancel(self, execution_id: str) -> bool:
        if execution_id in self._executions:
            self._executions[execution_id]["status"] = "cancelled"
            return True
        return False

    async def health_check(self) -> bool:
        return True

    def _get_browser_manager(self):
        """获取浏览器管理器"""
        # 返回本地浏览器管理器实例
        pass

    def _create_initial_state(self, state_spec: dict) -> dict:
        """创建初始状态"""
        state = {}
        for key, spec in state_spec.items():
            if 'initial' in spec:
                state[key] = spec['initial']
            elif spec['type'] == 'array':
                state[key] = []
            elif spec['type'] == 'string':
                state[key] = ""
            else:
                state[key] = None
        return state

    def _extract_outputs(self, outputs_spec: dict, final_state: dict) -> dict:
        """从最终状态提取输出"""
        # 解析 ${state.xxx} 引用
        pass
```

---

## 5. 云端执行器实现

```python
# services/cloud-backend/backend/app/agent/executor.py

import time
import uuid
import json
from typing import AsyncIterator

from agent_core.runtime.interfaces import (
    ExecutorInterface, RuntimeType, RuntimeContext,
    ExecutionRequest, ExecutionResponse, AgentEvent
)
from agent_core.graph.loader import GraphLoader
from agent_core.graph.compiler import GraphCompiler
from agent_core.tools.registry import ToolRegistry
from agent_core.resource.resolver import CloudAssetResolver

from celery import shared_task


class CloudExecutor(ExecutorInterface):
    """云端执行器 - FastAPI 后端"""

    runtime_type = RuntimeType.CLOUD

    def __init__(self, db, redis, config: dict, browser_pool=None):
        self.db = db
        self.redis = redis
        self.config = config
        self.browser_pool = browser_pool
        self.graph_loader = GraphLoader(
            definitions_path=config.get('definitions_path', 'agent-definitions')
        )
        self.tool_registry = ToolRegistry(RuntimeType.CLOUD)
        self.compiler = GraphCompiler(self.tool_registry)

    def _create_context(self, request: ExecutionRequest) -> RuntimeContext:
        """创建运行时上下文"""
        return RuntimeContext(
            runtime_type=RuntimeType.CLOUD,
            user_id=request.user_id,
            inputs=request.inputs,
            model_default=self._get_user_model(request.user_id),
            model_fast='claude-3-5-haiku-20241022',
            api_keys={
                "anthropic": self.config.get('anthropic_api_key'),
            },
            asset_resolver=CloudAssetResolver(self.config, request.user_id),
            extra={
                "db": self.db,
                "redis": self.redis,
                "browser_pool": self.browser_pool,
            }
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """同步执行（短任务）"""
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or f"tr-{uuid.uuid4()}"
        start_time = time.time()

        try:
            definition = self.graph_loader.load(request.graph_name)
            ctx = self._create_context(request)
            graph = self.compiler.compile(definition, ctx)
            initial_state = self._create_initial_state(definition['spec']['state'])
            final_state = await graph.ainvoke(initial_state)
            outputs = self._extract_outputs(definition['spec']['outputs'], final_state)

            return ExecutionResponse(
                success=True,
                outputs=outputs,
                execution_id=execution_id,
                execution_time=time.time() - start_time,
                runtime_type=self.runtime_type,
                trace_id=trace_id,
            )

        except Exception as e:
            return ExecutionResponse(
                success=False,
                outputs=None,
                error=str(e),
                execution_id=execution_id,
                execution_time=time.time() - start_time,
                runtime_type=self.runtime_type,
                trace_id=trace_id,
            )

    async def execute_async(self, request: ExecutionRequest) -> str:
        """异步执行（长任务，提交到 Celery）"""
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or f"tr-{uuid.uuid4()}"

        # 保存初始状态
        await self.redis.hset(f"execution:{execution_id}", mapping={
            "status": "pending",
            "trace_id": trace_id,
            "graph_name": request.graph_name,
            "created_at": time.time(),
        })

        # 提交到 Celery 队列
        execute_graph_task.delay(
            execution_id=execution_id,
            trace_id=trace_id,
            graph_name=request.graph_name,
            inputs=request.inputs,
            user_id=request.user_id,
        )

        return execution_id

    async def execute_stream(
        self, request: ExecutionRequest
    ) -> AsyncIterator[AgentEvent]:
        """流式执行，通过 SSE 返回"""
        # 实现类似 LocalExecutor 的流式执行
        pass

    def _get_user_model(self, user_id: str) -> str:
        """根据用户订阅级别获取模型"""
        # 查询用户订阅级别
        # Pro 用户可用 claude-opus-4-20250514
        return 'claude-sonnet-4-20250514'

    async def get_status(self, execution_id: str) -> dict:
        status = await self.redis.hgetall(f"execution:{execution_id}")
        return status or {"status": "not_found"}

    async def cancel(self, execution_id: str) -> bool:
        await self.redis.set(f"execution:{execution_id}:cancel", "1", ex=3600)
        return True

    async def health_check(self) -> bool:
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


@shared_task(bind=True)
def execute_graph_task(
    self,
    execution_id: str,
    trace_id: str,
    graph_name: str,
    inputs: dict,
    user_id: str
):
    """Celery 异步任务"""
    import asyncio

    async def run():
        from backend.app.core.deps import get_db, get_redis, get_browser_pool
        from backend.app.core.config import settings

        async with get_db() as db:
            redis = await get_redis()
            browser_pool = await get_browser_pool()

            executor = CloudExecutor(db, redis, settings.dict(), browser_pool)

            # 更新状态
            await redis.hset(f"execution:{execution_id}", mapping={
                "status": "running",
                "started_at": time.time(),
            })

            try:
                request = ExecutionRequest(
                    graph_name=graph_name,
                    inputs=inputs,
                    user_id=user_id,
                    trace_id=trace_id,
                )
                response = await executor.execute(request)

                await redis.hset(f"execution:{execution_id}", mapping={
                    "status": "completed" if response.success else "failed",
                    "outputs": json.dumps(response.outputs),
                    "error": response.error or "",
                    "completed_at": time.time(),
                })

            except Exception as e:
                await redis.hset(f"execution:{execution_id}", mapping={
                    "status": "failed",
                    "error": str(e),
                    "completed_at": time.time(),
                })

    asyncio.run(run())
```

---

## 6. Layer 1: Graph 定义规范

### 6.1 Graph 定义示例

```yaml
# agent-definitions/content-creation.yaml
apiVersion: agent/v1
kind: Graph
metadata:
  name: content-creation
  version: "1.0.0"
  description: "内容创作工作流"

spec:
  # 输入参数定义
  inputs:
    topic:
      type: string
      required: true
      description: "创作主题"
    platform:
      type: string
      required: true
      enum: [xiaohongshu, douyin, weibo, wechat_mp, bilibili]
    style:
      type: string
      default: "casual"
      enum: [casual, professional, humorous, educational]
    keywords:
      type: array
      items: string
      default: []

  # 状态定义
  state:
    stage:
      type: string
      initial: "init"
    research_results:
      type: array
    outline:
      type: string
    draft:
      type: string
    polished_content:
      type: string
    images:
      type: array
    final_content:
      type: string
    final_title:
      type: string
    error:
      type: string

  # 节点定义
  nodes:
    - name: research
      tool: web_search
      params:
        query: "${inputs.topic} ${inputs.platform} 热门内容 最新趋势"
        num_results: 10
      outputs:
        research_results: "$.results"

    - name: outline
      tool: llm_generate
      params:
        model: "${runtime.model.default}"
        system: "你是一个专业的自媒体内容策划师"
        prompt: |
          基于以下研究资料，为主题「${inputs.topic}」创建内容大纲。
          目标平台: ${inputs.platform}
          写作风格: ${inputs.style}
          研究资料: ${state.research_results}
      outputs:
        outline: "$.content"

    - name: draft
      tool: llm_generate
      params:
        model: "${runtime.model.default}"
        max_tokens: 8192
        prompt: |
          根据以下大纲撰写完整内容。
          平台: ${inputs.platform}
          大纲: ${state.outline}
      outputs:
        draft: "$.content"

    - name: polish
      tool: llm_generate
      params:
        model: "${runtime.model.default}"
        prompt: "润色以下内容: ${state.draft}"
      outputs:
        polished_content: "$.content"

    - name: generate_images
      tool: image_gen
      capability:
        required: false        # 非必需工具
        fallback: skip         # 不可用时跳过
      params:
        prompt: "为文章生成配图: ${state.polished_content[:200]}"
        count: 3
      outputs:
        images: "$.image_urls"

    - name: review
      tool: llm_generate
      params:
        model: "${runtime.model.default}"
        prompt: "审核内容质量: ${state.polished_content}"
      outputs:
        review_result: "$.result"

  # 边定义（工作流）
  edges:
    - from: START
      to: research
    - from: research
      to: outline
    - from: outline
      to: draft
    - from: draft
      to: polish
    - from: polish
      to: generate_images
    - from: generate_images
      to: review
    - from: review
      to: END
      condition: "${state.review_result.passed == true}"
    - from: review
      to: polish
      condition: "${state.review_result.passed == false && state.revision_count < 3}"

  # 输出定义
  outputs:
    content: "${state.polished_content}"
    title: "${state.final_title}"
    images: "${state.images}"
```

### 6.2 Graph 加载器

```python
# packages/agent-core/src/agent_core/graph/loader.py

from typing import Any
from pathlib import Path
import yaml
import json


class GraphLoader:
    """Graph 定义加载器"""

    def __init__(self, definitions_path: str = "agent-definitions"):
        self.definitions_path = Path(definitions_path)
        self._cache: dict[str, dict] = {}

    def load(self, graph_name: str) -> dict:
        """加载 Graph 定义"""
        if graph_name in self._cache:
            return self._cache[graph_name]

        yaml_path = self.definitions_path / f"{graph_name}.yaml"
        json_path = self.definitions_path / f"{graph_name}.json"

        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                definition = yaml.safe_load(f)
        elif json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                definition = json.load(f)
        else:
            raise FileNotFoundError(f"Graph definition not found: {graph_name}")

        self._validate(definition)
        self._cache[graph_name] = definition
        return definition

    def _validate(self, definition: dict):
        """验证 Graph 定义"""
        required_fields = ['apiVersion', 'kind', 'metadata', 'spec']
        for field in required_fields:
            if field not in definition:
                raise ValueError(f"Missing required field: {field}")

        if definition['kind'] != 'Graph':
            raise ValueError(f"Invalid kind: {definition['kind']}")

    def list_graphs(self) -> list[str]:
        """列出所有可用的 Graph"""
        graphs = []
        for path in self.definitions_path.glob("*.yaml"):
            graphs.append(path.stem)
        for path in self.definitions_path.glob("*.json"):
            if path.stem not in graphs:
                graphs.append(path.stem)
        return graphs
```

---

## 7. 统一资源 URI 方案

### 7.1 资源 URI 设计

```yaml
URI 格式:
  asset://{runtime}/{type}/{id}

示例:
  - asset://local/image/abc123         # 本地图片
  - asset://cloud/image/abc123         # 云端图片
  - asset://local/credential/xiaohongshu_user1  # 本地凭证
  - asset://cloud/credential/xiaohongshu_user1  # 云端凭证
  - asset://local/temp/draft_001       # 本地临时文件
  - asset://cloud/storage/user123/file # 云端用户存储
```

### 7.2 资源解析器

```python
# packages/agent-core/src/agent_core/resource/resolver.py

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import uuid

from .uri import AssetURI


class AssetResolver(ABC):
    """资源解析器基类"""

    @abstractmethod
    async def resolve(self, uri: str) -> str:
        """将 URI 解析为实际路径/URL"""
        pass

    @abstractmethod
    async def store(self, type: str, data: bytes, id: Optional[str] = None) -> str:
        """存储资源并返回 URI"""
        pass


class LocalAssetResolver(AssetResolver):
    """本地资源解析器"""

    def __init__(self, config: dict):
        self.base_path = Path(config.get('data_path', '~/.ai-creator/data')).expanduser()

    async def resolve(self, uri: str) -> str:
        asset = AssetURI.parse(uri)

        if asset.runtime == "cloud":
            # 云端资源需要下载到本地
            return await self._download_cloud_asset(asset)

        return str(self.base_path / asset.type / asset.id)

    async def store(self, type: str, data: bytes, id: Optional[str] = None) -> str:
        if id is None:
            id = str(uuid.uuid4())

        dir_path = self.base_path / type
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / id
        file_path.write_bytes(data)

        return f"asset://local/{type}/{id}"

    async def _download_cloud_asset(self, asset: AssetURI) -> str:
        """下载云端资源到本地缓存"""
        # 实现云端资源下载
        pass


class CloudAssetResolver(AssetResolver):
    """云端资源解析器"""

    def __init__(self, config: dict, user_id: str):
        self.config = config
        self.user_id = user_id
        self.s3_bucket = config.get('s3_bucket', 'ai-creator-assets')

    async def resolve(self, uri: str) -> str:
        asset = AssetURI.parse(uri)

        if asset.runtime == "local":
            raise ValueError("Local asset not available in cloud runtime")

        return await self._generate_presigned_url(asset)

    async def store(self, type: str, data: bytes, id: Optional[str] = None) -> str:
        import boto3

        if id is None:
            id = str(uuid.uuid4())

        s3_key = f"{self.user_id}/{type}/{id}"

        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=data,
        )

        return f"asset://cloud/{type}/{id}"

    async def _generate_presigned_url(self, asset: AssetURI) -> str:
        import boto3

        s3_key = f"{self.user_id}/{asset.type}/{asset.id}"

        s3_client = boto3.client('s3')
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.s3_bucket, 'Key': s3_key},
            ExpiresIn=3600,
        )

        return url
```

---

## 8. 部署策略

### 8.1 开发环境

```bash
# 克隆仓库
git clone https://github.com/your-org/ai-creator.git
cd ai-creator

# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 初始化 workspace（安装所有依赖）
uv sync

# 开发 Sidecar
cd apps/sidecar
uv run python -m sidecar.main

# 开发云端
cd services/cloud-backend
uv run uvicorn backend.app.main:app --reload
```

### 8.2 Sidecar 打包（桌面端）

```bash
# 方式 1: PyInstaller 打包为单文件
cd apps/sidecar
uv run pyinstaller --onefile --name ai-creator-sidecar src/sidecar/main.py

# 方式 2: Nuitka 编译（更好的性能）
uv run nuitka --standalone --onefile src/sidecar/main.py

# 输出: dist/ai-creator-sidecar (可执行文件)
# 放入 Tauri 的 sidecar 目录
```

### 8.3 云端部署（Docker）

```dockerfile
# services/cloud-backend/Dockerfile

FROM python:3.11-slim

# 安装 uv
RUN pip install uv

WORKDIR /app

# 复制 workspace 配置
COPY pyproject.toml uv.lock ./
COPY packages/agent-core ./packages/agent-core
COPY services/cloud-backend ./services/cloud-backend
COPY agent-definitions ./agent-definitions

# 安装依赖
RUN uv sync --frozen --package ai-creator-cloud

# 运行
CMD ["uv", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.4 发布到 PyPI（可选）

如果需要将 `agent-core` 发布为独立包：

```bash
# 构建
cd packages/agent-core
uv build

# 发布到 PyPI
uv publish --token $PYPI_TOKEN

# 其他项目可以直接安装
pip install agent-core
```

---

## 9. 开发规范

### 9.1 工具能力声明规范

```python
# 每个工具必须声明能力和支持的运行时
@ToolRegistry.register("my_tool", RuntimeType.LOCAL)
class MyLocalTool(ToolInterface):
    metadata = ToolMetadata(
        name="my_tool",
        description="工具描述",
        capabilities=[ToolCapability.XXX],
        supported_runtimes=[RuntimeType.LOCAL],  # 仅本地
        fallback_tool="fallback_tool_name",       # 降级方案
    )
```

### 9.2 运行时上下文使用规范

```python
# ❌ 错误做法：硬编码配置
class BadTool(ToolInterface):
    async def execute(self, **kwargs):
        api_key = os.environ.get("ANTHROPIC_API_KEY")  # 直接读环境变量

# ✅ 正确做法：从上下文获取
class GoodTool(ToolInterface):
    async def execute(self, ctx: RuntimeContext, **kwargs):
        api_key = ctx.api_keys.get("anthropic")  # 从上下文获取
```

### 9.3 资源 URI 使用规范

```python
# ❌ 禁止硬编码路径
image_path = "/Users/mac/.ai-creator/images/abc.png"

# ✅ 使用统一 URI
image_uri = "asset://local/image/abc"
# 或
image_uri = await ctx.asset_resolver.store("image", image_data)
```

---

## 10. LLM 统一接口设计

> 更新: 2025-12-28 | 云端LLM网关已完成开发，桌面端通过统一接口调用

### 10.1 设计理念

**核心原则**: agent-core 提供统一的 LLM 调用接口，屏蔽端云实现差异。

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM 统一接口架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    agent-core: LLMClientInterface                     │  │
│  │                         (统一调用接口)                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  - chat(messages, model, ...)       → LLMResponse              │  │  │
│  │  │  - chat_stream(messages, model, ...)→ AsyncIterator[str]       │  │  │
│  │  │  - get_available_models()           → List[ModelInfo]          │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│              ┌───────────────────────┴───────────────────────┐              │
│              │                                               │              │
│              ▼                                               ▼              │
│  ┌─────────────────────────┐                 ┌─────────────────────────┐   │
│  │   CloudLLMClient        │                 │   DirectLLMClient       │   │
│  │   (桌面端/Sidecar)       │                 │   (云端服务)             │   │
│  │                         │                 │                         │   │
│  │  ┌───────────────────┐  │                 │  ┌───────────────────┐  │   │
│  │  │ HTTP/HTTPS 调用   │  │                 │  │ 直接SDK调用       │  │   │
│  │  │ 云端 LLM 网关     │  │                 │  │ LLMGateway 实例   │  │   │
│  │  └───────────────────┘  │                 │  └───────────────────┘  │   │
│  └────────────┬────────────┘                 └────────────┬────────────┘   │
│               │                                           │                │
│               │  API Token + baseUrl                      │  内部调用       │
│               ▼                                           ▼                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      云端 LLM 网关 (已完成)                           │   │
│  │   - OpenAI 兼容接口: POST /v1/chat/completions                      │   │
│  │   - Anthropic 兼容接口: POST /v1/messages                           │   │
│  │   - 多供应商故障转移、熔断器、用量追踪                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 接口定义

```python
# packages/agent-core/src/agent_core/llm/interface.py

from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterator, List
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(str, Enum):
    """LLM 供应商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ALIBABA = "alibaba"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str                    # gpt-4o, claude-3-5-sonnet
    provider: LLMProvider
    display_name: str
    max_tokens: int
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tools: bool = True


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMUsage:
    """Token 使用统计"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    usage: LLMUsage
    cost: float = 0.0
    latency_ms: int = 0
    finish_reason: str = "stop"


@dataclass
class LLMConfig:
    """LLM 客户端配置"""
    # 网关配置
    base_url: str                    # LLM 网关地址
    api_token: str                   # API Token (sk-cf-xxx)

    # 环境配置
    environment: str = "production"  # development | production

    # 默认参数
    default_model: str = "claude-sonnet-4-20250514"
    default_max_tokens: int = 4096
    default_temperature: float = 0.7

    # 超时配置
    timeout_seconds: int = 120
    retry_count: int = 3

    # 可选: 直接调用配置 (云端使用)
    direct_mode: bool = False        # 是否直接调用 (跳过 HTTP)


class LLMClientInterface(ABC):
    """
    LLM 客户端统一接口

    - 端侧实现: CloudLLMClient (HTTP 调用云端网关)
    - 云端实现: DirectLLMClient (直接调用 LLMGateway)
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """
        发送对话请求

        Args:
            messages: 对话消息列表
            model: 模型名称 (可选, 使用默认模型)
            system: 系统提示 (可选)
            max_tokens: 最大生成 tokens (可选)
            temperature: 温度参数 (可选)
            user_id: 用户ID (用于用量追踪)

        Returns:
            LLMResponse: 响应结果
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        流式对话请求

        Yields:
            str: 逐字返回的内容片段
        """
        pass

    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """
        获取可用模型列表

        Returns:
            List[ModelInfo]: 模型信息列表
        """
        pass

    @abstractmethod
    async def get_usage_summary(
        self,
        user_id: str,
        period: str = "month"
    ) -> dict:
        """
        获取用量汇总

        Args:
            user_id: 用户ID
            period: 统计周期 (day, week, month)

        Returns:
            dict: 用量统计数据
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 网关是否可用
        """
        pass
```

### 10.3 桌面端实现 (CloudLLMClient)

```python
# packages/agent-core/src/agent_core/llm/cloud_client.py

import aiohttp
import json
from typing import List, Optional, AsyncIterator

from .interface import (
    LLMClientInterface, LLMConfig, LLMMessage,
    LLMResponse, LLMUsage, ModelInfo
)


class CloudLLMClient(LLMClientInterface):
    """
    云端 LLM 客户端 - 桌面端/Sidecar 使用

    通过 HTTP 调用云端 LLM 网关，支持 OpenAI 兼容格式。
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            )
        return self._session

    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """发送对话请求 (OpenAI 兼容格式)"""
        session = await self._get_session()

        # 构建消息
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        # 构建请求体
        payload = {
            "model": model or self.config.default_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature or self.config.default_temperature,
            "stream": False,
        }
        if user_id:
            payload["user"] = user_id

        # 发送请求
        url = f"{self.config.base_url}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise LLMError(f"LLM request failed: {response.status} - {error}")

            data = await response.json()

        # 解析响应
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider="cloud",
            usage=LLMUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式对话请求"""
        session = await self._get_session()

        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model or self.config.default_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature or self.config.default_temperature,
            "stream": True,
        }

        url = f"{self.config.base_url}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise LLMError(f"LLM stream request failed: {response.status}")

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def get_available_models(self) -> List[ModelInfo]:
        """获取可用模型列表"""
        session = await self._get_session()
        url = f"{self.config.base_url}/api/v1/llm/models"

        async with session.get(url) as response:
            if response.status != 200:
                return []
            data = await response.json()

        return [
            ModelInfo(
                model_id=m["model_id"],
                provider=m["provider"],
                display_name=m["display_name"],
                max_tokens=m.get("max_tokens", 4096),
                supports_streaming=m.get("supports_streaming", True),
                supports_vision=m.get("supports_vision", False),
            )
            for m in data.get("models", [])
        ]

    async def get_usage_summary(
        self,
        user_id: str,
        period: str = "month"
    ) -> dict:
        """获取用量汇总"""
        session = await self._get_session()
        url = f"{self.config.base_url}/api/v1/llm/usage/summary"
        params = {"period": period}

        async with session.get(url, params=params) as response:
            if response.status != 200:
                return {}
            return await response.json()

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            url = f"{self.config.base_url}/health"
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()


class LLMError(Exception):
    """LLM 调用异常"""
    pass
```

### 10.4 云端实现 (DirectLLMClient)

```python
# packages/agent-core/src/agent_core/llm/direct_client.py

from typing import List, Optional, AsyncIterator

from .interface import (
    LLMClientInterface, LLMConfig, LLMMessage,
    LLMResponse, LLMUsage, ModelInfo
)


class DirectLLMClient(LLMClientInterface):
    """
    直接调用 LLM 客户端 - 云端服务使用

    直接调用 LLMGateway 实例，无需 HTTP 开销。
    """

    def __init__(self, gateway: "LLMGateway", config: LLMConfig):
        """
        Args:
            gateway: LLMGateway 实例 (云端服务注入)
            config: LLM 配置
        """
        self.gateway = gateway
        self.config = config

    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """直接调用 LLMGateway"""
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await self.gateway.chat(
            messages=api_messages,
            model_id=model or self.config.default_model,
            user_id=user_id,
            system=system,
            max_tokens=max_tokens or self.config.default_max_tokens,
            temperature=temperature or self.config.default_temperature,
            stream=False,
        )

        return LLMResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,
            usage=LLMUsage(
                input_tokens=response.usage["input_tokens"],
                output_tokens=response.usage["output_tokens"],
                total_tokens=response.usage["input_tokens"] + response.usage["output_tokens"],
            ),
            cost=response.cost,
            latency_ms=response.latency_ms,
        )

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """直接调用 LLMGateway 流式接口"""
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        async for chunk in self.gateway.chat_stream(
            messages=api_messages,
            model_id=model or self.config.default_model,
            user_id=user_id,
            system=system,
            max_tokens=max_tokens or self.config.default_max_tokens,
            temperature=temperature or self.config.default_temperature,
        ):
            yield chunk

    async def get_available_models(self) -> List[ModelInfo]:
        """从数据库获取模型列表"""
        models = await self.gateway.get_available_models()
        return [
            ModelInfo(
                model_id=m.model_id,
                provider=m.provider,
                display_name=m.display_name,
                max_tokens=m.max_tokens,
                supports_streaming=m.supports_streaming,
                supports_vision=m.supports_vision,
            )
            for m in models
        ]

    async def get_usage_summary(
        self,
        user_id: str,
        period: str = "month"
    ) -> dict:
        """从用量追踪器获取统计"""
        return await self.gateway.usage_tracker.get_usage_summary(
            user_id, period
        )

    async def health_check(self) -> bool:
        """检查网关状态"""
        return True  # 直接调用，始终可用
```

### 10.5 配置管理

> 更新: 2025-12-28 | 桌面端用户登录后自动获取 API Token，无需手动配置

```python
# packages/agent-core/src/agent_core/llm/config.py

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from .interface import LLMConfig


class LLMConfigManager:
    """
    LLM 配置管理器

    - 桌面端: 用户登录后自动获取并保存 API Token
    - 无需手动配置，Token 由服务端分发
    - 支持开发/生产环境切换 (仅开发者使用)
    """

    # 默认配置路径
    DEFAULT_CONFIG_PATH = "~/.ai-creator/llm-config.json"

    # 默认网关地址 (固定，用户无需配置)
    DEFAULT_URLS = {
        "development": "http://localhost:8001",
        "production": "https://api.ai-creator.com",
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(
            config_path or os.path.expanduser(self.DEFAULT_CONFIG_PATH)
        )
        self._config: Optional[LLMConfig] = None

    def load(self, environment: str = "production") -> LLMConfig:
        """
        加载配置

        Args:
            environment: 环境名称 (development | production)

        Returns:
            LLMConfig: LLM 配置
        """
        # 从配置文件读取 (自动保存的 Token)
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            env_config = data.get(environment, {})
            return LLMConfig(
                base_url=self.DEFAULT_URLS[environment],  # 固定地址
                api_token=env_config.get("api_token", ""),
                environment=environment,
                default_model=env_config.get("default_model", "claude-sonnet-4-20250514"),
                timeout_seconds=env_config.get("timeout_seconds", 120),
            )

        # 返回默认配置 (无 Token，需要登录)
        return LLMConfig(
            base_url=self.DEFAULT_URLS[environment],
            api_token="",
            environment=environment,
        )

    def save_token(self, api_token: str, environment: str = "production"):
        """
        保存 API Token (用户登录后自动调用)

        Args:
            api_token: 服务端分发的 API Token (sk-cf-xxx)
            environment: 环境名称
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有配置
        data = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = json.load(f)

        # 更新 Token
        if environment not in data:
            data[environment] = {}
        data[environment]["api_token"] = api_token

        # 写入配置
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

        # 设置文件权限 (仅所有者可读写)
        self.config_path.chmod(0o600)

    def clear_token(self, environment: str = "production"):
        """
        清除 Token (用户登出时调用)
        """
        if not self.config_path.exists():
            return

        with open(self.config_path, 'r') as f:
            data = json.load(f)

        if environment in data:
            data[environment]["api_token"] = ""

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def is_logged_in(self, environment: str = "production") -> bool:
        """检查用户是否已登录 (是否有 Token)"""
        config = self.load(environment)
        return bool(config.api_token)

    def get_current_environment(self) -> str:
        """获取当前环境"""
        return os.environ.get("AI_CREATOR_ENV", "production")
```

### 10.6 桌面端配置文件示例

> 用户登录后自动生成，无需手动创建

```json
// ~/.ai-creator/llm-config.json (自动生成)
{
  "production": {
    "api_token": "sk-cf-xxxxxxxxxxxxxx"
  }
}
```

### 10.7 登录流程集成

```python
# apps/sidecar/src/sidecar/auth.py

from agent_core.llm.config import LLMConfigManager


async def on_user_login(user_token: str, api_base_url: str):
    """
    用户登录成功后的回调

    Args:
        user_token: 用户登录 Token (JWT)
        api_base_url: 云端 API 地址
    """
    import aiohttp

    # 1. 调用云端接口获取 LLM API Token
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/api/v1/auth/llm-token",
            headers={"Authorization": f"Bearer {user_token}"},
        ) as response:
            if response.status == 200:
                data = await response.json()
                api_token = data["api_token"]

                # 2. 自动保存到本地配置
                config_manager = LLMConfigManager()
                config_manager.save_token(api_token)

                return True

    return False


async def on_user_logout():
    """用户登出时清除 Token"""
    config_manager = LLMConfigManager()
    config_manager.clear_token()
```

更新后的 LLM 工具使用统一接口：

```python
# packages/agent-core/src/agent_core/tools/builtin/llm.py

from ..base import ToolInterface, ToolMetadata, ToolCapability, ToolResult
from ..registry import ToolRegistry
from ...runtime.interfaces import RuntimeContext
from ...llm.interface import LLMMessage


@ToolRegistry.register_universal("llm_generate")
class LLMGenerateTool(ToolInterface):
    """
    LLM 文本生成工具 - 端云统一

    自动根据运行时环境选择:
    - 桌面端: 使用 CloudLLMClient (HTTP 调用云端网关)
    - 云端: 使用 DirectLLMClient (直接调用 LLMGateway)
    """

    metadata = ToolMetadata(
        name="llm_generate",
        description="使用 LLM 生成文本",
        capabilities=[ToolCapability.LLM_GENERATE],
    )

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> ToolResult:
        """执行 LLM 生成"""

        # 从运行时上下文获取 LLM 客户端
        llm_client = ctx.extra.get("llm_client")
        if not llm_client:
            return ToolResult(
                success=False,
                data=None,
                error="LLM client not configured"
            )

        try:
            messages = [LLMMessage(role="user", content=prompt)]

            response = await llm_client.chat(
                messages=messages,
                model=model or ctx.model_default,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                user_id=ctx.user_id,
            )

            return ToolResult(
                success=True,
                data={
                    "content": response.content,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "cost": response.cost,
                }
            )

        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "用户提示"},
                "system": {"type": "string", "description": "系统提示"},
                "model": {"type": "string", "description": "模型名称"},
                "max_tokens": {"type": "integer", "default": 4096},
                "temperature": {"type": "number", "default": 0.7},
            },
            "required": ["prompt"]
        }
```

### 10.8 运行时上下文更新

```python
# packages/agent-core/src/agent_core/runtime/interfaces.py (更新)

@dataclass
class RuntimeContext:
    """运行时上下文 - 统一端云配置注入"""
    runtime_type: RuntimeType
    user_id: str
    inputs: dict

    # 模型配置
    model_default: str = "claude-sonnet-4-20250514"
    model_fast: str = "claude-3-5-haiku-20241022"

    # 🔥 LLM 客户端 (新增)
    # 由端/云实现注入，统一接口
    llm_client: Optional["LLMClientInterface"] = None

    # 资源解析器（由端/云实现注入）
    asset_resolver: Optional["AssetResolver"] = None

    # 额外上下文（端/云特有）
    extra: dict = field(default_factory=dict)
```

### 10.9 端侧执行器初始化示例

```python
# apps/sidecar/src/sidecar/executor.py (更新)

from agent_core.llm.cloud_client import CloudLLMClient
from agent_core.llm.config import LLMConfigManager


class LocalExecutor(ExecutorInterface):
    """本地执行器 - 桌面端 Python Sidecar"""

    def __init__(self, config: dict):
        self.config = config

        # 初始化 LLM 客户端
        llm_config_manager = LLMConfigManager()
        llm_config = llm_config_manager.load(
            environment=config.get('environment', 'production')
        )
        self.llm_client = CloudLLMClient(llm_config)

        # ... 其他初始化代码 ...

    def _create_context(self, request: ExecutionRequest) -> RuntimeContext:
        """创建运行时上下文"""
        return RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id=request.user_id,
            inputs=request.inputs,
            model_default=self.config.get('default_model', 'claude-sonnet-4-20250514'),
            model_fast=self.config.get('fast_model', 'claude-3-5-haiku-20241022'),
            llm_client=self.llm_client,  # 🔥 注入 LLM 客户端
            asset_resolver=LocalAssetResolver(self.config),
            extra={
                "browser_manager": self._get_browser_manager(),
            }
        )
```

### 10.10 云端执行器初始化示例

```python
# services/cloud-backend/backend/app/agent/executor.py (更新)

from agent_core.llm.direct_client import DirectLLMClient
from agent_core.llm.interface import LLMConfig


class CloudExecutor(ExecutorInterface):
    """云端执行器 - FastAPI 后端"""

    def __init__(self, db, redis, config: dict, browser_pool=None, llm_gateway=None):
        self.llm_gateway = llm_gateway

        # 初始化直接调用客户端
        llm_config = LLMConfig(
            base_url="",  # 直接调用不需要
            api_token="",
            direct_mode=True,
        )
        self.llm_client = DirectLLMClient(llm_gateway, llm_config)

        # ... 其他初始化代码 ...

    def _create_context(self, request: ExecutionRequest) -> RuntimeContext:
        """创建运行时上下文"""
        return RuntimeContext(
            runtime_type=RuntimeType.CLOUD,
            user_id=request.user_id,
            inputs=request.inputs,
            model_default=self._get_user_model(request.user_id),
            model_fast='claude-3-5-haiku-20241022',
            llm_client=self.llm_client,  # 🔥 注入 LLM 客户端
            asset_resolver=CloudAssetResolver(self.config, request.user_id),
            extra={
                "db": self.db,
                "redis": self.redis,
                "browser_pool": self.browser_pool,
            }
        )
```

### 10.11 agent-core 包结构更新

```text
packages/agent-core/src/agent_core/
├── __init__.py
│
├── llm/                                # 🔥 新增: LLM 统一接口层
│   ├── __init__.py
│   ├── interface.py                    # LLMClientInterface 抽象接口
│   ├── cloud_client.py                 # CloudLLMClient (HTTP 调用)
│   ├── direct_client.py                # DirectLLMClient (直接调用)
│   └── config.py                       # LLMConfigManager 配置管理
│
├── graph/                              # Graph 定义层
│   └── ...
├── runtime/                            # 运行时层
│   └── ...
├── tools/                              # 工具层
│   └── ...
├── resource/                           # 资源管理
│   └── ...
└── platforms/                          # 平台适配器
    └── ...
```

---

## 11. 总结

### 11.1 架构优势

| 特性 | 实现方式 |
|------|---------|
| **代码共享** | `agent-core` 包，uv workspace 管理 |
| **版本同步** | Monorepo 单一仓库，自动同步 |
| **端云对等** | 统一接口，不同实现 |
| **工具隔离** | ToolRegistry 按运行时注册 |
| **资源统一** | AssetURI 统一资源标识 |
| **部署灵活** | PyInstaller 打包 / Docker 部署 / PyPI 发布 |

### 11.2 开发流程

```text
1. 修改 agent-core → 端侧/云端自动生效
2. 开发端侧工具 → 注册到 RuntimeType.LOCAL
3. 开发云端工具 → 注册到 RuntimeType.CLOUD
4. 定义 Graph → 自动在端侧/云端运行
5. 打包发布 → Sidecar 二进制 / Docker 镜像
```

---

## 相关文档

- [系统架构](./01-系统架构.md)
- [桌面端设计](./02-桌面端设计.md)
- [云端服务设计](./04-云端服务设计.md)
- [平台适配器](./06-平台适配器.md)
- [AI工作流](./07-AI工作流.md)
- [BettaFish舆情分析集成](./08-BettaFish舆情分析集成.md)
- [开发规范](./11-开发规范.md)
