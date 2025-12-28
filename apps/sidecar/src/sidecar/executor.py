"""
本地执行器 - 在 Sidecar 中执行 Graph
@author Ysf
"""

import uuid
import time
from typing import AsyncIterator, Dict, Any

from agent_core.runtime.interfaces import (
    ExecutorInterface,
    RuntimeType,
    ExecutionRequest,
    ExecutionResponse,
)
from agent_core.runtime.context import RuntimeContext
from agent_core.runtime.events import AgentEvent, EventType
from agent_core.graph.loader import GraphLoader
from agent_core.graph.compiler import GraphCompiler
from agent_core.tools.registry import ToolRegistry
from agent_core.tools.builtin import LLMGenerateTool


class LocalExecutor(ExecutorInterface):
    """
    本地执行器

    在 Sidecar 环境中执行 Graph，提供完整的 AI Agent 运行时。

    特性：
    - 本地加载和编译 Graph
    - 本地执行工具
    - 支持流式输出
    - 完整的事件追踪
    """

    runtime_type = RuntimeType.LOCAL

    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地执行器

        Args:
            config: 配置字典
                - definitions_path: Graph 定义文件目录
                - api_keys: API 密钥字典
        """
        self.config = config

        # 初始化 Graph 加载器
        definitions_path = config.get("definitions_path", "agent-definitions")
        self.graph_loader = GraphLoader(definitions_path)

        # 初始化工具注册表
        self.tool_registry = ToolRegistry(RuntimeType.LOCAL)

        # 注册内置工具
        self._register_builtin_tools()

        # 初始化编译器
        self.compiler = GraphCompiler(self.tool_registry)

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        # 注册 LLM 工具
        llm_tool = LLMGenerateTool()
        self.tool_registry.register_tool(llm_tool)

        # TODO: 注册更多内置工具
        # - web_search
        # - storage
        # - image_gen
        # 等

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        执行 Graph（同步模式）

        Args:
            request: 执行请求

        Returns:
            执行响应
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or str(uuid.uuid4())

        try:
            # 1. 加载 Graph 定义
            graph_def = self.graph_loader.load(request.graph_name)

            # 2. 创建运行时上下文
            ctx = self._create_runtime_context(request, trace_id, execution_id)

            # 3. 编译 Graph
            compiled_graph = self.compiler.compile(graph_def, ctx)

            # 4. 准备初始状态
            initial_state = compiled_graph.initial_state_template.copy()

            # 5. 执行 Graph
            final_state = await compiled_graph.graph.ainvoke(initial_state)

            # 6. 提取输出
            outputs = self._extract_outputs(graph_def, final_state)

            # 7. 计算执行时间
            execution_time = time.time() - start_time

            # 8. 返回成功响应
            return ExecutionResponse(
                success=True,
                outputs=outputs,
                execution_id=execution_id,
                trace_id=trace_id,
                execution_time=execution_time,
                runtime_type=RuntimeType.LOCAL,
                metadata={
                    "graph_name": request.graph_name,
                    "final_state": final_state,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResponse(
                success=False,
                outputs=None,
                error=str(e),
                execution_id=execution_id,
                trace_id=trace_id,
                execution_time=execution_time,
                runtime_type=RuntimeType.LOCAL,
            )

    async def execute_stream(
        self, request: ExecutionRequest
    ) -> AsyncIterator[AgentEvent]:
        """
        执行 Graph（流式模式）

        Args:
            request: 执行请求

        Yields:
            AgentEvent: 执行过程中的事件流
        """
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or str(uuid.uuid4())

        try:
            # 发送开始事件
            yield AgentEvent(
                type=EventType.EXECUTION_START,
                data={
                    "graph_name": request.graph_name,
                    "execution_id": execution_id,
                    "trace_id": trace_id,
                },
            )

            # 1. 加载 Graph 定义
            graph_def = self.graph_loader.load(request.graph_name)

            # 2. 创建运行时上下文
            ctx = self._create_runtime_context(request, trace_id, execution_id)

            # 3. 编译 Graph
            compiled_graph = self.compiler.compile(graph_def, ctx)

            # 4. 准备初始状态
            initial_state = compiled_graph.initial_state_template.copy()

            # 5. 流式执行 Graph
            async for event in compiled_graph.graph.astream_events(
                initial_state, version="v1"
            ):
                # 转换 LangGraph 事件为 AgentEvent
                agent_event = self._convert_langgraph_event(event, execution_id)
                if agent_event:
                    yield agent_event

            # 发送完成事件
            yield AgentEvent(
                type=EventType.EXECUTION_COMPLETE,
                data={
                    "execution_id": execution_id,
                    "trace_id": trace_id,
                },
            )

        except Exception as e:
            # 发送错误事件
            yield AgentEvent(
                type=EventType.EXECUTION_ERROR,
                data={
                    "execution_id": execution_id,
                    "trace_id": trace_id,
                    "error": str(e),
                },
            )

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 表示健康，False 表示异常
        """
        try:
            # 检查 Graph 加载器
            graphs = self.graph_loader.list_graphs()

            # 检查工具注册表
            tools = self.tool_registry.list_tools()

            return True
        except Exception:
            return False

    def _create_runtime_context(
        self, request: ExecutionRequest, trace_id: str, run_id: str
    ) -> RuntimeContext:
        """
        创建运行时上下文

        Args:
            request: 执行请求
            trace_id: 追踪 ID
            run_id: 运行 ID

        Returns:
            RuntimeContext: 运行时上下文
        """
        # 从配置中获取 API 密钥
        api_keys = self.config.get("api_keys", {})

        # 创建上下文
        ctx = RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id=request.user_id,
            inputs=request.inputs,
            api_keys=api_keys,
            trace_id=trace_id,
            run_id=run_id,
            extra=request.extra,
        )

        return ctx

    def _extract_outputs(
        self, graph_def: Dict[str, Any], final_state: Dict[str, Any]
    ) -> Any:
        """
        从最终状态中提取输出

        Args:
            graph_def: Graph 定义
            final_state: 最终状态

        Returns:
            输出数据
        """
        spec = graph_def.get("spec", {})
        outputs_def = spec.get("outputs", {})

        if not outputs_def:
            # 如果没有定义输出，返回整个状态
            return final_state

        # TODO: 实现输出表达式求值
        # 当前简化版本：直接从 state 中提取
        outputs = {}
        for key, expr in outputs_def.items():
            if expr.startswith("${state."):
                # 提取状态变量名
                state_var = expr[8:-1]  # 去除 ${state. 和 }
                outputs[key] = final_state.get(state_var)
            else:
                outputs[key] = expr

        return outputs

    def _convert_langgraph_event(
        self, event: Dict[str, Any], execution_id: str
    ) -> AgentEvent | None:
        """
        转换 LangGraph 事件为 AgentEvent

        Args:
            event: LangGraph 事件
            execution_id: 执行 ID

        Returns:
            AgentEvent 或 None
        """
        event_type = event.get("event")

        if event_type == "on_chain_start":
            return AgentEvent(
                type=EventType.NODE_START,
                data={
                    "execution_id": execution_id,
                    "node_name": event.get("name"),
                },
            )
        elif event_type == "on_chain_end":
            return AgentEvent(
                type=EventType.NODE_COMPLETE,
                data={
                    "execution_id": execution_id,
                    "node_name": event.get("name"),
                    "output": event.get("data", {}).get("output"),
                },
            )
        elif event_type == "on_chain_error":
            return AgentEvent(
                type=EventType.NODE_ERROR,
                data={
                    "execution_id": execution_id,
                    "node_name": event.get("name"),
                    "error": str(event.get("data", {}).get("error")),
                },
            )

        return None

