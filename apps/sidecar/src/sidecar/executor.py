"""
本地执行器 - 在 Sidecar 中执行 Graph
@author Ysf
"""

import logging
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
from agent_core.skill import SkillManager
from agent_core.tools.browser import BrowserManager, NavigateTool, ScreenshotTool, ClickTool, TypeTool
from agent_core.discovery.service import DiscoveryService
from agent_core.tools.discovery import ListAgentsTool, GetAgentDetailsTool, ListToolsTool, GetToolDetailsTool
from agent_core.llm import LLMConfigManager, CloudLLMClient

logger = logging.getLogger(__name__)


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
        
        # 初始化 Skill 管理器 (假设 skills 在 agent-definitions/skills)
        from pathlib import Path
        skills_path = str(Path(definitions_path) / "skills")
        self.skill_manager = SkillManager([skills_path])
        
        # 初始化工具注册表
        self.tool_registry = ToolRegistry(RuntimeType.LOCAL)
        
        # Initialize Discovery Service
        self.discovery_service = DiscoveryService(self.graph_loader, self.tool_registry)

        # 初始化浏览器管理器 (Headless defaults to True, can be configured)
        # 桌面应用中可能希望看到浏览器 (headless=False) 方便调试或展示
        self.browser_manager = BrowserManager(headless=False)



        # 注册内置工具
        self._register_builtin_tools()

        # 初始化编译器 (注入 graph_loader 以支持 Subgraph)
        self.compiler = GraphCompiler(self.tool_registry, graph_loader=self.graph_loader)

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        # 注册 LLM 工具
        llm_tool = LLMGenerateTool()
        self.tool_registry.register_tool(llm_tool)

        # 注册 Discovery Tools
        for tool_cls in [ListAgentsTool, GetAgentDetailsTool, ListToolsTool, GetToolDetailsTool]:
            self.tool_registry.register_tool(tool_cls())

        # 注册 Mock 搜索工具 (Phase 1 演示用)
        from agent_core.tools.mock_search import MockSearchTool
        mock_search = MockSearchTool()
        self.tool_registry.register_tool(mock_search)

        # 注册浏览器工具
        self.tool_registry.register_tool(NavigateTool())
        self.tool_registry.register_tool(ScreenshotTool())
        self.tool_registry.register_tool(ClickTool())
        self.tool_registry.register_tool(TypeTool())
        
        # 注册工具执行器
        from agent_core.tools.builtin.tool_executor import ToolExecutionTool
        self.tool_registry.register_tool(ToolExecutionTool())

        # TODO: 注册更多内置工具
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
        import traceback

        start_time = time.time()
        execution_id = str(uuid.uuid4())
        trace_id = request.trace_id or str(uuid.uuid4())

        try:
            logger.info(f"Loading graph: {request.graph_name}")
            # 1. 加载 Graph 定义
            graph_def = self.graph_loader.load(request.graph_name)
            logger.info("Graph loaded successfully")

            # 2. 创建运行时上下文
            ctx = await self._create_runtime_context(request, trace_id, execution_id)
            
            # 2.1 装配技能
            skills = graph_def.get("spec", {}).get("skills", [])
            if skills:
                logger.info(f"Equipping skills: {skills}")
                self.skill_manager.equip_agent(ctx, skills)

            logger.info(f"Context created, inputs: {ctx.inputs}")

            # 3. 编译 Graph
            logger.info("Compiling graph...")
            compiled_graph = self.compiler.compile(graph_def, ctx)
            logger.info("Graph compiled successfully")

            # 4. 准备初始状态
            initial_state = compiled_graph.initial_state_template.copy()
            logger.info(f"Initial state: {initial_state}")

            # 5. 执行 Graph
            logger.info("Executing graph...")
            final_state = await compiled_graph.graph.ainvoke(initial_state)
            logger.info(f"Graph executed, final_state: {final_state}")

            # 6. 提取输出
            outputs = self._extract_outputs(graph_def, final_state, request.inputs)

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
            logger.error(f"Exception: {e}")
            logger.error(traceback.format_exc())
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
            ctx = await self._create_runtime_context(request, trace_id, execution_id)

            # 2.1 装配技能
            skills = graph_def.get("spec", {}).get("skills", [])
            if skills:
                # logger.info(f"Equipping skills: {skills}")
                self.skill_manager.equip_agent(ctx, skills)

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

    async def shutdown(self):
        """关闭执行器，释放资源"""
        if self.browser_manager:
            await self.browser_manager.stop()

    async def _create_runtime_context(
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

        # 从 LLM 配置中加载 API Token
        environment = self.config.get("environment", "production")
        llm_config_manager = LLMConfigManager()
        llm_config = llm_config_manager.load(environment)

        # 将 LLM API Token 作为 anthropic 密钥
        if llm_config.api_token:
            api_keys["anthropic"] = llm_config.api_token
            logger.info(f"Loaded API token from LLM config (env={environment})")
        else:
            logger.warning("No API token found in LLM config, LLM tools will fail")

        # 创建 LLM 客户端 (用于动态获取模型)
        llm_client = None
        model_default = "claude-opus-4-5-20251101-thinking"  # 后备默认值
        model_fast = "claude-haiku-4-5-20251001"  # 后备默认值

        if llm_config.api_token:
            llm_client = CloudLLMClient(llm_config)
            # 动态获取模型
            try:
                from agent_core.llm.interface import ModelType
                # 获取 REASONING 类型的模型作为 model_default
                reasoning_model = await llm_client.get_model_by_type(ModelType.REASONING)
                if reasoning_model:
                    model_default = reasoning_model.model_id
                    logger.info(f"Dynamic model_default: {model_default}")
                # 获取 TEXT 类型的模型作为 model_fast
                text_model = await llm_client.get_model_by_type(ModelType.TEXT)
                if text_model:
                    model_fast = text_model.model_id
                    logger.info(f"Dynamic model_fast: {model_fast}")
            except Exception as e:
                logger.warning(f"Failed to get dynamic models: {e}, using defaults")

        # 创建上下文
        ctx = RuntimeContext(
            runtime_type=RuntimeType.LOCAL,
            user_id=request.user_id,
            inputs=request.inputs,
            api_keys=api_keys,
            llm_client=llm_client,
            model_default=model_default,
            model_fast=model_fast,
            trace_id=trace_id,
            run_id=run_id,
            extra=request.extra,
        )
        
        # 注入浏览器管理器
        ctx.extra["browser_manager"] = self.browser_manager
        
        # 注入工具注册表 (供 LLMGenerateTool 获取工具定义)
        ctx.extra["tool_registry"] = self.tool_registry

        return ctx

    def _extract_outputs(
        self, graph_def: Dict[str, Any], final_state: Dict[str, Any], inputs: Dict[str, Any]
    ) -> Any:
        """
        从最终状态中提取输出

        Args:
            graph_def: Graph 定义
            final_state: 最终状态
            inputs: 输入参数

        Returns:
            输出数据
        """
        spec = graph_def.get("spec", {})
        outputs_def = spec.get("outputs", {})

        if not outputs_def:
            return final_state

        return self._evaluate_output_value(outputs_def, final_state, inputs)

    def _evaluate_output_value(
        self, value: Any, final_state: Dict[str, Any], inputs: Dict[str, Any]
    ) -> Any:
        """
        递归求值输出表达式

        Args:
            value: 待求值的值
            final_state: 最终状态
            inputs: 输入参数

        Returns:
            求值后的值
        """
        if isinstance(value, str):
            if value.startswith("${state.") and value.endswith("}"):
                state_var = value[8:-1]
                return final_state.get(state_var)
            elif value.startswith("${inputs.") and value.endswith("}"):
                input_var = value[9:-1]
                return inputs.get(input_var)
            return value
        elif isinstance(value, dict):
            return {k: self._evaluate_output_value(v, final_state, inputs) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._evaluate_output_value(item, final_state, inputs) for item in value]
        return value

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

