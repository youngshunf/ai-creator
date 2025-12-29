"""
Graph 编译器 - 将 Graph 定义编译为 LangGraph
@author Ysf
"""

import logging
from typing import Dict, Any, Callable, List

from jsonpath_ng import parse as jsonpath_parse
from langgraph.graph import StateGraph, END

from .types import CompiledGraph, NodeExecutionContext
from ..runtime.context import RuntimeContext
from ..runtime.expression import ExpressionEvaluator
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class GraphCompiler:
    """
    Graph 编译器

    将声明式的 Graph 定义编译为可执行的 LangGraph StateGraph。

    编译流程：
    1. 解析 Graph 定义
    2. 为每个节点创建执行函数
    3. 构建 StateGraph
    4. 添加节点和边
    5. 返回 CompiledGraph
    """

    def __init__(self, tool_registry: ToolRegistry, graph_loader: Any = None):
        """
        初始化编译器

        Args:
            tool_registry: 工具注册表
            graph_loader: Graph 加载器 (用于加载子图)
        """
        self.tool_registry = tool_registry
        self.graph_loader = graph_loader

    def compile(
        self, definition: Dict[str, Any], ctx: RuntimeContext
    ) -> CompiledGraph:
        """
        编译 Graph 定义

        Args:
            definition: Graph 定义字典
            ctx: 运行时上下文

        Returns:
            CompiledGraph: 编译后的 Graph

        Raises:
            GraphCompileError: 编译失败
        """
        spec = definition.get("spec", {})
        metadata = definition.get("metadata", {})

        # 创建表达式求值器
        evaluator = ExpressionEvaluator(ctx)

        # 创建 StateGraph
        state_graph = StateGraph(dict)

        # 创建节点函数映射
        node_functions: Dict[str, Callable] = {}

        # 为每个节点创建执行函数
        nodes = spec.get("nodes", [])
        for node_def in nodes:
            node_name = node_def.get("name")
            if not node_name:
                continue

            # 创建节点函数
            node_func = self._create_node_function(node_def, ctx, evaluator)
            node_functions[node_name] = node_func

            # 添加节点到 StateGraph
            state_graph.add_node(node_name, node_func)

        # 添加边
        edges = spec.get("edges", [])
        self._add_edges(state_graph, edges, evaluator, ctx)

        # 设置入口点
        self._set_entry_point(state_graph, edges)

        # 编译 StateGraph
        compiled = state_graph.compile()

        # 创建初始状态模板
        initial_state_template = self._create_initial_state_template(spec)

        # 返回编译结果
        return CompiledGraph(
            graph=compiled,
            metadata=metadata,
            initial_state_template=initial_state_template,
            node_functions=node_functions,
        )

    def _create_node_function(
        self,
        node_def: Dict[str, Any],
        ctx: RuntimeContext,
        evaluator: ExpressionEvaluator,
    ) -> Callable:
        """
        为节点创建执行函数

        Args:
            node_def: 节点定义
            ctx: 运行时上下文
            evaluator: 表达式求值器

        Returns:
            节点执行函数
        """
        # 判断是 Tool 节点还是 Agent 节点
        if node_def.get("agent"):
            return self._create_agent_node_function(node_def, ctx, evaluator)
        else:
            return self._create_tool_node_function(node_def, ctx, evaluator)

    def _create_agent_node_function(
        self,
        node_def: Dict[str, Any],
        ctx: RuntimeContext,
        evaluator: ExpressionEvaluator,
    ) -> Callable:
        """创建子 Agent (Subgraph) 执行函数"""
        node_name = node_def.get("name")
        agent_name = node_def.get("agent")
        inputs_mapping = node_def.get("inputs", {})  # 传递给子 Agent 的输入
        outputs_mapping = node_def.get("outputs", {})
        condition_expr = node_def.get("condition")

        async def agent_node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"[Node:{node_name}] Starting Subgraph execution, agent={agent_name}")

            # 1. 检查条件
            if condition_expr:
                condition_result = evaluator.evaluate(condition_expr, ctx.inputs, state)
                if not condition_result:
                    logger.info(f"[Node:{node_name}] Skipped (condition not met)")
                    return state

            # 2. 检查 GraphLoader
            if not self.graph_loader:
                raise GraphCompileError(f"无法执行子 Agent '{agent_name}': GraphCompiler 未配置 GraphLoader")

            # 3. 加载并编译子 Graph
            # 注意: 这里每次执行都重新编译可能会有性能开销，建议后续增加 compiled_cache
            try:
                sub_graph_def = self.graph_loader.load(agent_name)
                # 递归编译
                # 注意: 避免深层递归导致栈溢出，应有深度限制检查 (暂略)
                sub_compiler = GraphCompiler(self.tool_registry, self.graph_loader)
                # 为子 Graph 创建独立的 Context? 
                # 通常子 Graph 共享 Runtime 环境 (如 API Keys), 但 inputs 是独立的
                # 我们这里使用父 Context，但 inputs 会被覆盖为子 Graph 的输入
                # 为了不污染父 Context，我们复制一个 ctx (浅拷贝即可)
                from copy import copy
                sub_ctx = copy(ctx)
                
                # 计算子 Graph 的输入
                # inputs_mapping 里的 value 是表达式，需要在 Parent Context 下求值
                sub_inputs = {}
                for key, expr in inputs_mapping.items():
                    sub_inputs[key] = evaluator.evaluate(expr, ctx.inputs, state)
                
                sub_ctx.inputs = sub_inputs
                
                # 编译
                sub_compiled_graph = sub_compiler.compile(sub_graph_def, sub_ctx)
                
            except Exception as e:
                raise GraphCompileError(f"子图 '{agent_name}' 加载或编译失败: {str(e)}")

            # 4. 执行子 Graph
            logger.info(f"[Node:{node_name}] Invoking Subgraph: {agent_name}")
            try:
                # 构造初始 state
                initial_state = sub_compiled_graph.initial_state_template.copy()
                # LangGraph 启动时会自动合并 initial state，我们只需要传入 dict
                
                # 执行
                # 注意: sub_compiled_graph.graph 是一个 Runnable
                # 我们传入 initial_state 作为 input (LangGraph 约定)
                sub_result = await sub_compiled_graph.graph.ainvoke(initial_state)
                
                logger.info(f"[Node:{node_name}] Subgraph execution succeeded")
                
            except Exception as e:
                 logger.error(f"[Node:{node_name}] Subgraph execution failed: {str(e)}")
                 raise GraphCompileError(f"子图 execution 失败: {str(e)}")

            # 5. 提取输出并更新父 State
            if outputs_mapping:
                # 子图的结果 sub_result 通常就是最终的 State Dict
                extracted_outputs = self._extract_outputs(
                    outputs_mapping, sub_result, state
                )
                state.update(extracted_outputs)
            
            return state

        return agent_node_function

    def _create_tool_node_function(
        self,
        node_def: Dict[str, Any],
        ctx: RuntimeContext,
        evaluator: ExpressionEvaluator,
    ) -> Callable:
        """创建工具节点执行函数 (原 _create_node_function 逻辑)"""
        node_name = node_def.get("name")
        tool_name = node_def.get("tool")
        params_template = node_def.get("params", {})
        outputs_mapping = node_def.get("outputs", {})
        condition_expr = node_def.get("condition")

        async def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            节点执行函数

            Args:
                state: 当前状态

            Returns:
                更新后的状态
            """
            logger.info(f"[Node:{node_name}] Starting execution, tool={tool_name}")

            # 检查条件（如果有）
            if condition_expr:
                condition_result = evaluator.evaluate(
                    condition_expr, ctx.inputs, state
                )
                if not condition_result:
                    logger.info(f"[Node:{node_name}] Skipped (condition not met)")
                    return state

            # 求值参数
            params = evaluator.evaluate_params(params_template, ctx.inputs, state)
            logger.debug(f"[Node:{node_name}] Params: {params}")

            # 获取工具
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise GraphCompileError(f"工具未找到: {tool_name}")

            # 执行工具
            logger.info(f"[Node:{node_name}] Executing tool: {tool_name}")
            result = await tool.execute(ctx, **params)

            # 检查执行结果
            if not result.success:
                logger.error(f"[Node:{node_name}] Tool execution failed: {result.error}")
                raise GraphCompileError(f"工具执行失败: {tool_name}, 错误: {result.error}")

            logger.info(f"[Node:{node_name}] Tool execution succeeded")
            logger.debug(f"[Node:{node_name}] Result data: {result.data}")

            # 提取输出并更新状态
            if outputs_mapping:
                extracted_outputs = self._extract_outputs(
                    outputs_mapping, result.data, state
                )
                state.update(extracted_outputs)
                logger.debug(f"[Node:{node_name}] Updated state: {state}")

            return state

        return node_function

    def _extract_outputs(
        self,
        outputs_mapping: Dict[str, str],
        tool_result: Any,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        从工具返回值中提取输出

        使用 JSON Path 语法提取字段。

        Args:
            outputs_mapping: 输出映射定义 {"state_var": "$.json.path"}
            tool_result: 工具返回值
            state: 当前状态

        Returns:
            提取的输出字典
        """
        extracted = {}

        for state_var, json_path_expr in outputs_mapping.items():
            # 检查是否是追加模式 (key 以 + 开头)
            is_append = False
            if state_var.startswith("+"):
                state_var = state_var[1:]
                is_append = True

            value = None
            if json_path_expr.startswith("$"):
                # JSON Path 提取
                try:
                    jsonpath_expr_obj = jsonpath_parse(json_path_expr)
                    matches = jsonpath_expr_obj.find(tool_result)
                    if matches:
                        # 取第一个匹配结果
                        value = matches[0].value
                except Exception as e:
                    raise GraphCompileError(
                        f"JSON Path 解析失败: {json_path_expr}, 错误: {e}"
                    ) from e
            else:
                # 直接赋值
                value = json_path_expr

            # 设置或追加值
            if is_append:
                if state_var not in extracted:
                     extracted[state_var] = [] # Initialize if not present in this extraction batch
                
                # Note: This logic assumes 'extracted' will be merged into 'state' properly.
                # Use a special marker or handle update logic in caller.
                # Actually, caller does: state.update(extracted)
                # If we return {"messages": [new_msg]}, dict.update will overwrite.
                
                # So we must read from current STATE.
                # But _extract_outputs takes 'state' as arg.
                current_val = state.get(state_var, [])
                if not isinstance(current_val, list):
                    current_val = []
                
                if isinstance(value, list):
                    extracted[state_var] = current_val + value
                elif value is not None:
                     current_val.append(value)
                     extracted[state_var] = current_val
            else:
                extracted[state_var] = value

        return extracted

    def _add_edges(
        self,
        state_graph: StateGraph,
        edges: List[Dict[str, Any]],
        evaluator: ExpressionEvaluator,
        ctx: RuntimeContext,
    ) -> None:
        """
        添加边到 StateGraph

        Args:
            state_graph: StateGraph 实例
            edges: 边定义列表
            evaluator: 表达式求值器
            ctx: 运行时上下文
        """
        # Group edges by source node
        edges_by_source: Dict[str, List[Dict[str, Any]]] = {}
        for edge_def in edges:
            from_node = edge_def.get("from")
            if not from_node or from_node == "START":
                continue
            if from_node not in edges_by_source:
                edges_by_source[from_node] = []
            edges_by_source[from_node].append(edge_def)

        for from_node, node_edges in edges_by_source.items():
            # Check if any edge is conditional
            is_conditional = any(e.get("condition") for e in node_edges)
            
            if is_conditional:
                # Create a router function
                # Use a closure factory to capture node_edges and ctx/evaluator
                def create_router(edges_list):
                    def router(state: Dict[str, Any]) -> str:
                        for edge in edges_list:
                            condition_expr = edge.get("condition")
                            to_node = edge.get("to")
                            if to_node == "END":
                                to_node_mapped = END
                            else:
                                to_node_mapped = to_node

                            if condition_expr:
                                if evaluator.evaluate(condition_expr, ctx.inputs, state):
                                    return to_node_mapped
                            else:
                                # Unconditional edge acts as 'else' or fallback
                                return to_node_mapped
                        
                        # No condition matched
                        # LangGraph might error if None is returned, or stop?
                        # Returning END is permitted if desired, but better to be explicit in Graph.
                        # For now, return END if no match (dead end prevention)
                        return END

                    return router

                router_func = create_router(node_edges)
                
                # Build path map
                path_map = {}
                for edge in node_edges:
                    to_node = edge.get("to")
                    to_node_mapped = END if to_node == "END" else to_node
                    path_map[to_node_mapped] = to_node_mapped
                
                # Add conditional edges
                # Note: condition_func is not passed here, but a 'router'.
                # LangGraph signature: add_conditional_edges(source, path, path_map=None)
                state_graph.add_conditional_edges(from_node, router_func, path_map)
            
            else:
                # All edges are unconditional? 
                # Ideally only one unconditional edge allowed per node in valid Graphs.
                # If multiple, it's ambiguous. GraphValidator should catch this (but doesn't yet).
                # Take the first one.
                first_edge = node_edges[0]
                to_node = first_edge.get("to")
                if to_node == "END":
                    to_node = END
                state_graph.add_edge(from_node, to_node)

    def _set_entry_point(
        self, state_graph: StateGraph, edges: List[Dict[str, Any]]
    ) -> None:
        """
        设置入口点

        查找从 START 出发的边，设置为入口点。

        Args:
            state_graph: StateGraph 实例
            edges: 边定义列表
        """
        for edge_def in edges:
            if edge_def.get("from") == "START":
                entry_node = edge_def.get("to")
                if entry_node and entry_node != "END":
                    state_graph.set_entry_point(entry_node)
                    return

        # 如果没有找到 START 边，抛出错误
        raise GraphCompileError("未找到入口点（从 START 出发的边）")

    def _create_initial_state_template(
        self, spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建初始状态模板

        Args:
            spec: Graph spec

        Returns:
            初始状态字典
        """
        initial_state = {}

        # 从 state 定义中提取默认值
        state_defs = spec.get("state", {})
        for state_name, state_def in state_defs.items():
            if isinstance(state_def, dict):
                default_value = state_def.get("default")
                if default_value is not None:
                    initial_state[state_name] = default_value

        return initial_state


class GraphCompileError(Exception):
    """Graph 编译错误"""

    pass

