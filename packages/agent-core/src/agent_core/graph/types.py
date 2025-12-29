"""
Graph 类型定义 - 定义 Graph 相关的数据结构
@author Ysf
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Callable, Union

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph


@dataclass
class CompiledGraph:
    """
    编译后的 Graph

    包含 LangGraph 的编译后 StateGraph 对象、元数据和初始状态模板。
    """

    # LangGraph 编译后的 StateGraph 对象
    graph: Union[StateGraph, CompiledStateGraph]

    # Graph 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 初始状态模板
    initial_state_template: Dict[str, Any] = field(default_factory=dict)

    # 节点函数映射（调试用）
    node_functions: Dict[str, Callable] = field(default_factory=dict)


@dataclass
class NodeExecutionContext:
    """
    节点执行上下文

    传递给节点函数的上下文信息。
    """

    # 节点名称
    node_name: str

    # 工具名称
    tool_name: str

    # Graph 输入参数
    inputs: Dict[str, Any]

    # 当前状态
    state: Dict[str, Any]

    # 运行时上下文
    runtime_context: Any  # RuntimeContext 类型

    # 节点参数（已求值）
    params: Dict[str, Any] = field(default_factory=dict)

    # 输出映射定义
    outputs_mapping: Dict[str, str] = field(default_factory=dict)
