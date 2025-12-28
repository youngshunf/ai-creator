"""
Graph 加载器 - 加载 YAML/JSON 格式的 Agent 定义
@author Ysf
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from .validator import GraphValidator, ValidationResult


class GraphLoader:
    """
    Graph 加载器

    负责从文件系统加载 Graph 定义（YAML/JSON 格式），
    并进行验证和缓存。

    示例:
        loader = GraphLoader("agent-definitions")
        graph_def = loader.load("content-creation")
    """

    def __init__(
        self,
        definitions_path: str = "agent-definitions",
        validator: Optional[GraphValidator] = None,
    ):
        """
        初始化 GraphLoader

        Args:
            definitions_path: Graph 定义文件目录
            validator: GraphValidator 实例（可选）
        """
        self.definitions_path = Path(definitions_path)
        self.validator = validator or GraphValidator()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load(self, graph_name: str) -> Dict[str, Any]:
        """
        加载 Graph 定义

        优先从缓存读取，缓存未命中则从文件加载。

        Args:
            graph_name: Graph 名称（不含扩展名）

        Returns:
            Graph 定义字典

        Raises:
            GraphNotFoundError: Graph 文件不存在
            GraphLoadError: 文件解析失败
            GraphValidationError: 验证失败
        """
        # 检查缓存
        if graph_name in self._cache:
            return self._cache[graph_name]

        # 从文件加载
        definition = self._load_from_file(graph_name)

        # 验证
        self._validate(definition, graph_name)

        # 缓存
        self._cache[graph_name] = definition

        return definition

    def reload(self, graph_name: str) -> Dict[str, Any]:
        """
        强制重新加载 Graph 定义

        忽略缓存，直接从文件读取并重新验证。

        Args:
            graph_name: Graph 名称

        Returns:
            Graph 定义字典
        """
        # 清除缓存
        if graph_name in self._cache:
            del self._cache[graph_name]

        # 重新加载
        return self.load(graph_name)

    def list_graphs(self) -> List[str]:
        """
        列出所有可用的 Graph

        Returns:
            Graph 名称列表（不含扩展名）
        """
        if not self.definitions_path.exists():
            return []

        graphs = set()
        for ext in [".yaml", ".yml", ".json"]:
            for file_path in self.definitions_path.glob(f"*{ext}"):
                graphs.add(file_path.stem)

        return sorted(graphs)

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._cache.clear()

    def _load_from_file(self, graph_name: str) -> Dict[str, Any]:
        """
        从文件加载 Graph 定义

        按优先级尝试加载: .yaml > .yml > .json

        Args:
            graph_name: Graph 名称

        Returns:
            Graph 定义字典

        Raises:
            GraphNotFoundError: 文件不存在
            GraphLoadError: 文件解析失败
        """
        # 按优先级查找文件
        for ext in [".yaml", ".yml", ".json"]:
            file_path = self.definitions_path / f"{graph_name}{ext}"
            if file_path.exists():
                return self._parse_file(file_path)

        # 未找到文件
        raise GraphNotFoundError(
            f"Graph '{graph_name}' 未找到，"
            f"路径: {self.definitions_path.absolute()}"
        )

    def _parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析 YAML 或 JSON 文件

        Args:
            file_path: 文件路径

        Returns:
            解析后的字典

        Raises:
            GraphLoadError: 解析失败
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 根据扩展名选择解析器
            if file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
            elif file_path.suffix == ".json":
                data = json.loads(content)
            else:
                raise GraphLoadError(
                    f"不支持的文件格式: {file_path.suffix}"
                )

            if not isinstance(data, dict):
                raise GraphLoadError(
                    f"Graph 定义必须是对象，实际类型: {type(data).__name__}"
                )

            return data

        except yaml.YAMLError as e:
            raise GraphLoadError(
                f"YAML 解析失败: {file_path.name}, 错误: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise GraphLoadError(
                f"JSON 解析失败: {file_path.name}, 错误: {e}"
            ) from e
        except Exception as e:
            raise GraphLoadError(
                f"文件加载失败: {file_path.name}, 错误: {e}"
            ) from e

    def _validate(self, definition: Dict[str, Any], graph_name: str) -> None:
        """
        验证 Graph 定义

        Args:
            definition: Graph 定义
            graph_name: Graph 名称

        Raises:
            GraphValidationError: 验证失败
        """
        result = self.validator.validate(definition)
        if not result.success:
            error_messages = "\n".join(
                f"  - {error.field}: {error.message}"
                for error in result.errors
            )
            raise GraphValidationError(
                f"Graph '{graph_name}' 验证失败:\n{error_messages}"
            )


class GraphNotFoundError(Exception):
    """Graph 未找到错误"""

    pass


class GraphLoadError(Exception):
    """Graph 加载错误"""

    pass


class GraphValidationError(Exception):
    """Graph 验证错误"""

    pass

