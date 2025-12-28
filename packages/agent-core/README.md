# Agent Core

AI Creator 核心 Agent 包，提供端云共享的 Graph 加载、编译、执行能力。

@author Ysf

## 功能

- Graph 加载器 (YAML/JSON)
- Graph 编译器 (编译为 LangGraph)
- Graph 验证器
- 运行时接口
- 工具注册表
- 统一资源 URI

## 使用

\`\`\`python
from agent_core.graph.loader import GraphLoader
from agent_core.runtime.interfaces import ExecutorInterface

# 加载 Graph
loader = GraphLoader()
graph = loader.load("content-creation.yaml")

# 执行
executor = LocalExecutor()  # 或 CloudExecutor
result = executor.execute("content-creation", inputs={})
\`\`\`

## 目录结构

\`\`\`
src/agent_core/
├── graph/          # Graph 加载/编译
├── runtime/        # 运行时接口
├── tools/          # 工具层基类
├── resource/       # 资源管理
├── crypto/         # 加密工具
└── platforms/      # 平台适配器
\`\`\`
