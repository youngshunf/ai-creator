"""
Graph 编译器 - 将 Graph 定义编译为 LangGraph
@author Ysf
"""

from typing import Dict, Any, Callable, List

from jsonpath_ng import parse as jsonpath_parse
from langgraph.graph import StateGraph, END

from .types import CompiledGraph, NodeExecutionContext
from ..runtime.context import RuntimeContext
from ..runtime.expression import ExpressionEvaluator
from ..tools.registry import ToolRegistry


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

    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化编译器

        Args:
            tool_registry: 工具注册表
        """
        self.tool_registry = tool_registry

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

        # 创建初始状态模板
        initial_state_template = self._create_initial_state_template(spec)

        # 返回编译结果
        return CompiledGraph(
            graph=state_graph,
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
            # 检查条件（如果有）
            if condition_expr:
                condition_result = evaluator.evaluate(
                    condition_expr, ctx.inputs, state
                )
                if not condition_result:
                    # 条件不满足，跳过执行
                    return state

            # 求值参数
            params = evaluator.evaluate_params(params_template, ctx.inputs, state)

            # 获取工具
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise GraphCompileError(f"工具未找到: {tool_name}")

            # 执行工具
            result = await tool.execute(ctx, **params)

            # 提取输出并更新状态
            if outputs_mapping:
                extracted_outputs = self._extract_outputs(
                    outputs_mapping, result.data, state
                )
                state.update(extracted_outputs)

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
            if json_path_expr.startswith("$"):
                # JSON Path 提取
                try:
                    jsonpath_expr = jsonpath_parse(json_path_expr)
                    matches = jsonpath_expr.find(tool_result)
                    if matches:
                        # 取第一个匹配结果
                        extracted[state_var] = matches[0].value
                    else:
                        extracted[state_var] = None
                except Exception as e:
                    raise GraphCompileError(
                        f"JSON Path 解析失败: {json_path_expr}, 错误: {e}"
                    ) from e
            else:
                # 直接赋值
                extracted[state_var] = json_path_expr

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
        for edge_def in edges:
            from_node = edge_def.get("from")
            to_node = edge_def.get("to")
            condition_expr = edge_def.get("condition")

            if not from_node or not to_node:
                continue

            # 特殊处理 START 和 END
            if from_node == "START":
                # START 节点由 set_entry_point 处理
                continue

            if to_node == "END":
                to_node = END

            # 添加边
            if condition_expr:
                # 条件边
                def create_condition_func(expr):
                    def condition_func(state):
                        return evaluator.evaluate(expr, ctx.inputs, state)

                    return condition_func

                condition_func = create_condition_func(condition_expr)
                state_graph.add_conditional_edges(
                    from_node, condition_func, {True: to_node}
                )
            else:
                # 无条件边
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

