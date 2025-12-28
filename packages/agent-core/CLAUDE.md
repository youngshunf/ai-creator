# Agent Core - AI 上下文文档

> **路径**: `packages/agent-core/`
> **类型**: Python 共享包
> **作者**: @Ysf

---

## 📋 模块概览

**Agent Core** 是 AI Creator 的核心共享包，提供端云统一的 Agent Runtime 抽象层。

### 核心定位

- 端云共享代码的唯一来源
- 提供统一的 Agent 执行接口
- 屏蔽端云差异，保证行为一致

### 依赖关系

```
agent-core (无外部依赖)
    ↑
    ├── apps/sidecar (依赖 agent-core)
    └── services/cloud-backend (依赖 agent-core)
```

---

## 🏗️ 目录结构

```
packages/agent-core/
├── pyproject.toml                       # 包配置
├── README.md                            # 包说明
├── CLAUDE.md                            # 本文档
│
├── src/agent_core/                      # 源代码
│   ├── __init__.py                      # 模块导出
│   │
│   ├── runtime/                         # 运行时模块
│   │   ├── __init__.py                  # 导出接口
│   │   ├── interfaces.py                # 核心接口定义
│   │   └── router.py                    # 智能路由器
│   │
│   ├── graph/                           # Graph 模块
│   │   ├── __init__.py                  # 导出接口
│   │   ├── loader.py                    # Graph 加载器
│   │   ├── compiler.py                  # Graph 编译器
│   │   └── validator.py                 # Graph 验证器
│   │
│   ├── tools/                           # 工具模块
│   │   ├── __init__.py                  # 导出接口
│   │   ├── interfaces.py                # 工具接口
│   │   ├── registry.py                  # 工具注册表
│   │   └── builtin/                     # 内置工具
│   │       ├── __init__.py
│   │       ├── llm.py                   # LLM 工具
│   │       ├── search.py                # 搜索工具
│   │       └── storage.py               # 存储工具
│   │
│   ├── llm/                             # LLM 模块
│   │   ├── __init__.py                  # 导出接口
│   │   ├── config.py                    # 配置管理
│   │   ├── cloud_client.py              # 云端客户端 (HTTP)
│   │   └── direct_client.py             # 直接调用客户端
│   │
│   ├── platforms/                       # 平台适配器
│   │   ├── __init__.py                  # 导出接口
│   │   ├── base.py                      # 基类
│   │   ├── xiaohongshu.py               # 小红书
│   │   ├── douyin.py                    # 抖音
│   │   ├── bilibili.py                  # B站
│   │   ├── weibo.py                     # 微博
│   │   └── wechat_mp.py                 # 微信公众号
│   │
│   ├── resource/                        # 资源管理
│   │   ├── __init__.py                  # 导出接口
│   │   ├── resolver.py                  # URI 解析器
│   │   └── storage.py                   # 存储管理
│   │
│   └── crypto/                          # 加密工具
│       ├── __init__.py                  # 导出接口
│       ├── aes.py                       # AES 加密
│       └── credential.py                # 凭证加密
│
└── tests/                               # 单元测试
    ├── __init__.py
    ├── conftest.py                      # pytest 配置
    ├── test_runtime/                    # 运行时测试
    │   ├── __init__.py
    │   └── test_router.py               # 路由器测试
    └── test_platforms/                  # 平台测试
        ├── __init__.py
        ├── test_base.py                 # 基类测试
        └── test_xiaohongshu.py          # 小红书测试
```

---

## 🔧 核心接口

### 1. Runtime 接口

**文件**: `src/agent_core/runtime/interfaces.py`

```python
# 运行时类型
class RuntimeType(str, Enum):
    LOCAL = "local"    # 本地执行
    CLOUD = "cloud"    # 云端执行

# 执行请求
@dataclass
class ExecutionRequest:
    graph_name: str
    inputs: dict[str, Any]
    user_id: str
    session_id: Optional[str] = None
    timeout: int = 300
    trace_id: Optional[str] = None

# 执行响应
@dataclass
class ExecutionResponse:
    success: bool
    outputs: dict[str, Any]
    error: Optional[str] = None
    execution_id: str
    trace_id: str
    execution_time: float

# 执行器接口
class ExecutorInterface(ABC):
    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """同步执行 Graph"""
        pass

    @abstractmethod
    async def execute_stream(self, request: ExecutionRequest) -> AsyncIterator[AgentEvent]:
        """流式执行 Graph"""
        pass
```

### 2. Tool 接口

**文件**: `src/agent_core/tools/interfaces.py`

```python
# 工具接口
class ToolInterface(ABC):
    metadata: ToolMetadata

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """获取输入参数 Schema"""
        pass

# 工具注册表
class ToolRegistry:
    @classmethod
    def register(cls, name: str, runtime: RuntimeType):
        """注册工具"""
        pass

    @classmethod
    def get(cls, name: str, runtime: RuntimeType) -> ToolInterface:
        """获取工具"""
        pass
```

### 3. LLM 接口

**文件**: `src/agent_core/llm/__init__.py`

```python
# LLM 客户端接口
class LLMClientInterface(ABC):
    @abstractmethod
    async def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成文本"""
        pass

    @abstractmethod
    async def generate_stream(self, messages: List[LLMMessage], **kwargs) -> AsyncIterator[str]:
        """流式生成文本"""
        pass

# 云端客户端 (桌面端使用)
class CloudLLMClient(LLMClientInterface):
    """通过 HTTP 调用云端 LLM 网关"""
    pass

# 直接调用客户端 (云端使用)
class DirectLLMClient(LLMClientInterface):
    """直接调用 LLMGateway 实例"""
    pass
```

---

## 📦 依赖管理

### pyproject.toml

```toml
[project]
name = "agent-core"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "langchain>=0.1.0",
    "langgraph>=0.2.0",
    "anthropic>=0.40.0",
    "jsonpath-ng>=1.6.0",
    "simpleeval>=0.9.13",
    "cryptography>=42.0.0",
    "boto3>=1.34.0",
    "aiohttp>=3.9.0",
    "aiofiles>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_runtime/test_router.py

# 生成覆盖率报告
uv run pytest --cov=agent_core --cov-report=html
```

### 测试结构

```
tests/
├── conftest.py                          # pytest 配置
├── test_runtime/                        # 运行时测试
│   └── test_router.py                   # 路由器测试
└── test_platforms/                      # 平台测试
    ├── test_base.py                     # 基类测试
    └── test_xiaohongshu.py              # 小红书测试
```

---

## 🔗 关键文件

| 文件 | 说明 | 优先级 |
|------|------|--------|
| `__init__.py` | 模块导出 | P0 |
| `runtime/interfaces.py` | 核心接口定义 | P0 |
| `runtime/router.py` | 智能路由器 | P0 |
| `llm/config.py` | LLM 配置管理 | P0 |
| `llm/cloud_client.py` | 桌面端 LLM 客户端 | P0 |
| `llm/direct_client.py` | 云端 LLM 客户端 | P0 |
| `tools/interfaces.py` | 工具接口 | P0 |
| `tools/registry.py` | 工具注册表 | P0 |
| `platforms/base.py` | 平台适配器基类 | P1 |
| `platforms/xiaohongshu.py` | 小红书适配器 | P1 |

---

## 📚 相关文档

- [系统架构](../../docs/01-系统架构.md)
- [Agent Runtime](../../docs/05-Agent-Runtime.md)
- [开发规范](../../docs/11-开发规范.md)

---

## 🔼 导航

[← 返回根目录](../../CLAUDE.md)
