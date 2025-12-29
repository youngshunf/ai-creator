"""
Graph 验证器 - 验证 Graph 定义的正确性
@author Ysf
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional


@dataclass
class ValidationError:
    """验证错误"""

    field: str
    message: str
    line: Optional[int] = None


@dataclass
class ValidationWarning:
    """验证警告"""

    field: str
    message: str
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """验证结果"""

    success: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)


class GraphValidator:
    """
    Graph 验证器

    验证 Graph 定义的正确性，包括：
    - Schema 验证：必填字段、格式
    - 类型验证：数据类型
    - 引用验证：节点、工具引用
    - 图结构验证：连通性、循环检测
    - 表达式验证：语法、变量引用
    """

    # 支持的数据类型
    VALID_TYPES = {"string", "integer", "float", "boolean", "object", "array"}

    # 表达式正则
    EXPR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, tool_registry=None):
        """
        初始化验证器

        Args:
            tool_registry: 工具注册表（可选，用于验证工具引用）
        """
        self.tool_registry = tool_registry

    def validate(self, definition: Dict[str, Any]) -> ValidationResult:
        """
        验证 Graph 定义

        Args:
            definition: Graph 定义字典

        Returns:
            ValidationResult: 验证结果
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []

        # 1. Schema 验证
        errors.extend(self._validate_schema(definition))

        # 如果基础 Schema 验证失败，不继续后续验证
        if errors:
            return ValidationResult(success=False, errors=errors, warnings=warnings)

        # 2. 类型验证
        errors.extend(self._validate_types(definition))

        # 3. 图结构验证
        spec = definition.get("spec", {})
        errors.extend(self._validate_graph_structure(spec))

        # 4. 表达式验证
        errors.extend(self._validate_expressions(definition))

        # 5. 工具引用验证（如果有工具注册表）
        if self.tool_registry:
            errors.extend(self._validate_tool_references(spec))

        # 返回结果
        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _validate_schema(self, definition: Dict[str, Any]) -> List[ValidationError]:
        """
        验证 Schema：必填字段、格式

        Args:
            definition: Graph 定义

        Returns:
            错误列表
        """
        errors = []

        # 验证顶层必填字段
        required_fields = ["apiVersion", "kind", "metadata", "spec"]
        for field in required_fields:
            if field not in definition:
                errors.append(
                    ValidationError(field=field, message=f"缺少必填字段 '{field}'")
                )

        # 验证 apiVersion 格式
        api_version = definition.get("apiVersion", "")
        if api_version and not api_version.startswith("agent/"):
            errors.append(
                ValidationError(
                    field="apiVersion",
                    message=f"apiVersion 格式错误，期望 'agent/v1'，实际 '{api_version}'",
                )
            )

        # 验证 kind
        kind = definition.get("kind", "")
        if kind and kind != "Graph":
            errors.append(
                ValidationError(
                    field="kind", message=f"kind 必须为 'Graph'，实际 '{kind}'"
                )
            )

        # 验证 metadata
        metadata = definition.get("metadata", {})
        if isinstance(metadata, dict):
            if "name" not in metadata:
                errors.append(
                    ValidationError(field="metadata.name", message="缺少 Graph 名称")
                )

            if "version" not in metadata:
                errors.append(
                    ValidationError(field="metadata.version", message="缺少版本号")
                )
            elif not self._is_valid_version(metadata["version"]):
                errors.append(
                    ValidationError(
                        field="metadata.version",
                        message=f"版本号格式错误: {metadata['version']}",
                    )
                )

        # 验证 spec
        spec = definition.get("spec", {})
        if not isinstance(spec, dict):
            errors.append(
                ValidationError(field="spec", message="spec 必须是对象")
            )
        else:
            # 验证 spec.nodes 和 spec.edges
            if "nodes" not in spec:
                errors.append(
                    ValidationError(field="spec.nodes", message="缺少节点定义")
                )
            if "edges" not in spec:
                errors.append(
                    ValidationError(field="spec.edges", message="缺少边定义")
                )

        return errors

    def _validate_types(self, definition: Dict[str, Any]) -> List[ValidationError]:
        """
        验证类型定义

        Args:
            definition: Graph 定义

        Returns:
            错误列表
        """
        errors = []
        spec = definition.get("spec", {})

        # 验证 inputs 类型
        inputs = spec.get("inputs", {})
        if isinstance(inputs, dict):
            for name, input_def in inputs.items():
                if isinstance(input_def, dict):
                    input_type = input_def.get("type", "")
                    if input_type and input_type not in self.VALID_TYPES:
                        errors.append(
                            ValidationError(
                                field=f"spec.inputs.{name}.type",
                                message=f"无效的类型: {input_type}",
                            )
                        )

                    # 验证 required 字段
                    required = input_def.get("required")
                    if required is not None and not isinstance(required, bool):
                        errors.append(
                            ValidationError(
                                field=f"spec.inputs.{name}.required",
                                message="required 必须是布尔值",
                            )
                        )

        # 验证 state 类型
        state = spec.get("state", {})
        if isinstance(state, dict):
            for name, state_def in state.items():
                if isinstance(state_def, dict):
                    state_type = state_def.get("type", "")
                    if state_type and state_type not in self.VALID_TYPES:
                        errors.append(
                            ValidationError(
                                field=f"spec.state.{name}.type",
                                message=f"无效的类型: {state_type}",
                            )
                        )

        return errors

    def _validate_graph_structure(
        self, spec: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        验证图结构：连通性、循环检测

        Args:
            spec: Graph spec

        Returns:
            错误列表
        """
        errors = []

        nodes = spec.get("nodes", [])
        edges = spec.get("edges", [])

        if not isinstance(nodes, list) or not isinstance(edges, list):
            return errors

        # 构建节点集合
        node_names = set()
        for node in nodes:
            if isinstance(node, dict):
                name = node.get("name")
                if name:
                    if name in node_names:
                        errors.append(
                            ValidationError(
                                field=f"spec.nodes[{name}]",
                                message=f"节点名称重复: {name}",
                            )
                        )
                    node_names.add(name)
                else:
                    errors.append(
                        ValidationError(
                            field="spec.nodes", message="节点缺少 name 字段"
                        )
                    )

                # 验证节点必填字段
                if "tool" not in node:
                    errors.append(
                        ValidationError(
                            field=f"spec.nodes[{name}]", message="节点缺少 tool 字段"
                        )
                    )

        # 验证边引用的节点存在
        valid_node_names = node_names | {"START", "END"}
        for i, edge in enumerate(edges):
            if isinstance(edge, dict):
                from_node = edge.get("from")
                to_node = edge.get("to")

                if not from_node:
                    errors.append(
                        ValidationError(
                            field=f"spec.edges[{i}]", message="边缺少 from 字段"
                        )
                    )
                elif from_node not in valid_node_names:
                    errors.append(
                        ValidationError(
                            field=f"spec.edges[{i}].from",
                            message=f"引用了不存在的节点: {from_node}",
                        )
                    )

                if not to_node:
                    errors.append(
                        ValidationError(
                            field=f"spec.edges[{i}]", message="边缺少 to 字段"
                        )
                    )
                elif to_node not in valid_node_names:
                    errors.append(
                        ValidationError(
                            field=f"spec.edges[{i}].to",
                            message=f"引用了不存在的节点: {to_node}",
                        )
                    )

        # 验证图连通性
        if node_names:
            errors.extend(self._check_connectivity(node_names, edges))

        # 验证是否有循环
        errors.extend(self._check_cycles(node_names, edges))

        return errors

    def _check_connectivity(
        self, nodes: Set[str], edges: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """
        检查图的连通性

        Args:
            nodes: 节点集合
            edges: 边列表

        Returns:
            错误列表
        """
        errors = []

        # 构建邻接表
        adj: Dict[str, List[str]] = {node: [] for node in nodes}
        adj["START"] = []

        for edge in edges:
            if isinstance(edge, dict):
                from_node = edge.get("from")
                to_node = edge.get("to")
                if from_node and to_node and to_node != "END":
                    if from_node not in adj:
                        adj[from_node] = []
                    adj[from_node].append(to_node)

        # 从 START 开始 DFS
        visited = set()
        self._dfs(adj, "START", visited)

        # 检查是否所有节点都可达
        unreachable = nodes - visited
        if unreachable:
            errors.append(
                ValidationError(
                    field="spec.edges",
                    message=f"存在孤立节点（从 START 不可达）: {', '.join(unreachable)}",
                )
            )

        return errors

    def _dfs(self, adj: Dict[str, List[str]], node: str, visited: Set[str]) -> None:
        """
        深度优先搜索

        Args:
            adj: 邻接表
            node: 当前节点
            visited: 已访问节点集合
        """
        if node in visited or node == "END":
            return

        visited.add(node)
        for neighbor in adj.get(node, []):
            self._dfs(adj, neighbor, visited)

    def _check_cycles(
        self, nodes: Set[str], edges: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """
        检查图中是否存在循环（使用拓扑排序）

        Args:
            nodes: 节点集合
            edges: 边列表

        Returns:
            错误列表
        """
        # Agent Graph 允许循环 (如: planner -> executor -> planner)
        # 因此不再强制检查循环依赖
        return []

    def _validate_expressions(
        self, definition: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        验证表达式语法和引用

        Args:
            definition: Graph 定义

        Returns:
            错误列表
        """
        errors = []
        spec = definition.get("spec", {})

        # 收集所有合法的变量
        valid_vars = self._collect_valid_vars(spec)

        # 递归验证所有表达式
        errors.extend(self._validate_value_expressions(spec, valid_vars, "spec"))

        return errors

    def _collect_valid_vars(self, spec: Dict[str, Any]) -> Set[str]:
        """
        收集所有合法的变量引用

        Args:
            spec: Graph spec

        Returns:
            变量集合（格式: "inputs.xxx", "state.xxx", "runtime.xxx"）
        """
        valid_vars = set()

        # inputs
        inputs = spec.get("inputs", {})
        if isinstance(inputs, dict):
            for name in inputs.keys():
                valid_vars.add(f"inputs.{name}")

        # state
        state = spec.get("state", {})
        if isinstance(state, dict):
            for name in state.keys():
                valid_vars.add(f"state.{name}")

        # runtime (固定字段)
        runtime_fields = [
            "user_id",
            "runtime_type",
            "model_default",
            "model_fast",
            "trace_id",
            "run_id",
            "device_type",
        ]
        for field in runtime_fields:
            valid_vars.add(f"runtime.{field}")

        return valid_vars

    def _validate_value_expressions(
        self, value: Any, valid_vars: Set[str], path: str
    ) -> List[ValidationError]:
        """
        递归验证值中的表达式

        Args:
            value: 待验证的值
            valid_vars: 合法变量集合
            path: 当前路径（用于错误提示）

        Returns:
            错误列表
        """
        errors = []

        if isinstance(value, str):
            # 验证字符串中的表达式
            for match in self.EXPR_PATTERN.finditer(value):
                expr = match.group(1).strip()
                errors.extend(self._validate_single_expression(expr, valid_vars, path))

        elif isinstance(value, dict):
            # 递归验证字典
            for key, val in value.items():
                errors.extend(
                    self._validate_value_expressions(val, valid_vars, f"{path}.{key}")
                )

        elif isinstance(value, list):
            # 递归验证列表
            for i, item in enumerate(value):
                errors.extend(
                    self._validate_value_expressions(item, valid_vars, f"{path}[{i}]")
                )

        return errors

    def _validate_single_expression(
        self, expr: str, valid_vars: Set[str], path: str
    ) -> List[ValidationError]:
        """
        验证单个表达式

        Args:
            expr: 表达式内容
            valid_vars: 合法变量集合
            path: 当前路径

        Returns:
            错误列表
        """
        errors = []

        # 提取变量引用（简化版，只检查点号分隔的引用）
        # 例如：inputs.topic, state.outline, runtime.user_id
        var_pattern = re.compile(r"\b(inputs|state|runtime)\.(\w+)\b")
        for match in var_pattern.finditer(expr):
            var_ref = match.group(0)  # 如 "inputs.topic"
            if var_ref not in valid_vars:
                errors.append(
                    ValidationError(
                        field=path,
                        message=f"表达式引用了未定义的变量: {var_ref}",
                    )
                )

        return errors

    def _validate_tool_references(
        self, spec: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        验证工具引用

        Args:
            spec: Graph spec

        Returns:
            错误列表
        """
        errors = []

        nodes = spec.get("nodes", [])
        for node in nodes:
            if isinstance(node, dict):
                tool_name = node.get("tool")
                node_name = node.get("name", "unknown")

                if tool_name and not self.tool_registry.has_tool(tool_name):
                    errors.append(
                        ValidationError(
                            field=f"spec.nodes[{node_name}].tool",
                            message=f"工具未注册: {tool_name}",
                        )
                    )

        return errors

    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """
        验证版本号格式（语义化版本）

        Args:
            version: 版本号字符串

        Returns:
            是否合法
        """
        # 简化的语义化版本验证：major.minor.patch
        pattern = re.compile(r"^\d+\.\d+\.\d+$")
        return bool(pattern.match(version))

